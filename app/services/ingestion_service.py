from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from app.models.saved_reel import ReelStatus
from app.repositories import PlaceRepository, SavedReelRepository
from app.repositories.interfaces import PlaceCandidate, SavedReelCreate
from app.services.extraction_pipeline import ExtractionPipeline
from app.services.model_router import ModelChoice, ModelRouter
from app.services.places_verifier import GooglePlacesVerifier, VerifiedPlace
from app.services.media_storage import get_media_storage
import hashlib
import re
@dataclass(frozen=True)
class IngestionPlan:
    reel_url: str
    model_choice: ModelChoice


@dataclass(frozen= True)
class IngestionResult:
    saved_reel_id: int
    place_id: int
    verified_place: VerifiedPlace
    model_used: str



class IngestionValidationError(ValueError):
    pass    

class IngestionService:
    def __init__(
        self,
        *,
        place_repo: PlaceRepository,
        saved_reel_repo: SavedReelRepository,
        model_router: ModelRouter | None = None,
        extraction_pipeline: ExtractionPipeline | None = None,
        places_verifier: GooglePlacesVerifier | None = None,
    ) -> None:
        self.place_repo = place_repo
        self.saved_reel_repo = saved_reel_repo
        self.model_router = model_router or ModelRouter()
        self.extraction_pipeline = extraction_pipeline or ExtractionPipeline(
            model_router=self.model_router
        )
        self.places_verifier = places_verifier or GooglePlacesVerifier()

    async def plan_ingestion(
        self,
        *,
        reel_url: str,
        metadata_text: str | None = None,
        prefer_high_accuracy: bool = False,
    ) -> IngestionPlan:
        model_choice = self.model_router.select_model(
            metadata_text, prefer_high_accuracy=prefer_high_accuracy
        )
        return IngestionPlan(reel_url=reel_url, model_choice=model_choice)
    

    @staticmethod
    def normalize_url(url: str) -> str:
        # Strip query parameters that don't matter, e.g., ?igsh=123
        return re.sub(r"\?.*$", "", url).strip("/")

    @staticmethod
    def _extract_coordinates(location):
        """Extract latitude and longitude from a GeoAlchemy2 Point element."""
        import re
        # GeoAlchemy2 points can be returned as WKT strings like "POINT(lon lat)"
        # or as WKB binary (hex string)
        location_str = str(location)
        
        # Try WKT format first
        match = re.search(r'POINT\(([^ ]+)\s+([^ ]+)\)', location_str)
        if match:
            lon, lat = float(match.group(1)), float(match.group(2))
            return lat, lon
        
        # If it looks like hex (WKB binary), parse it using shapely
        if all(c in '0123456789abcdefABCDEF' for c in location_str):
            try:
                from shapely.wkb import loads
                geom = loads(bytes.fromhex(location_str))
                lon, lat = geom.coords[0]
                return lat, lon
            except Exception as e:
                raise ValueError(f"Could not parse WKB coordinates: {e}")
        
        raise ValueError(f"Could not extract coordinates from location: {location_str}")

    async def ingest_reel(
        self,
        *,
        reel_url: str,
        prefer_high_accuracy: bool = False,
    ) -> IngestionResult:
        
        normalized_url = self.normalize_url(reel_url)
        
        # 1. FAST VALIDATION CACHING (Dedup check)
        existing_reel = await self.saved_reel_repo.get_by_reel_url(normalized_url)
        
        if existing_reel and existing_reel.status == ReelStatus.processed and existing_reel.place:
            # We already have it, return the cached result instantly!
            place = existing_reel.place
            lat, lon = self._extract_coordinates(place.location)
            return IngestionResult(
                saved_reel_id=existing_reel.id,
                place_id=place.id,
                verified_place=VerifiedPlace(
                    google_place_id=place.google_place_id,
                    place_name=place.place_name,
                    formatted_address=place.formatted_address,
                    city=place.city,
                    region=place.region,
                    country=place.country,
                    latitude=lat,
                    longitude=lon,
                    score=existing_reel.ai_confidence or 1.0,
                ),
                model_used=existing_reel.ai_model_used or "cache",
            )
            
        # 2. RUN EXTRACTION PIPELINE
        # (It's new or previously failed)
        extraction = await self.extraction_pipeline.extract(
            reel_url=normalized_url,
            prefer_high_accuracy=prefer_high_accuracy,
        )

        verification = await self.places_verifier.resolve_best(extraction.candidates)
        if not verification.success or not verification.place:
            raise IngestionValidationError(
                verification.error or "Place verification failed"
            )
            
        verified = verification.place
        
        # 3. SAVE MEDIA TO STORAGE
        storage = get_media_storage()
        # Generate a stable unique key so reels don't overwrite each other (URL hash)
        url_hash = hashlib.md5(normalized_url.encode()).hexdigest()[:12]
        video_ext = extraction.raw_info.get("ext", "mp4")
        platform = extraction.metadata.platform or "unknown"
        destination_key = f"{platform}/{url_hash}/video.{video_ext}"
        
        # This writes it to either /tmp/roamy_media/... or s3://...
        stored_path = storage.store_file(extraction.video_path, destination_key)

        # 4. SAVE DB RECORDS
        place = await self.place_repo.get_or_create(
            PlaceCandidate(
                google_place_id=verified.google_place_id,
                place_name=verified.place_name,
                latitude=verified.latitude,
                longitude=verified.longitude,
                formatted_address=verified.formatted_address,
                city=verified.city,
                region=verified.region,
                country=verified.country,
            )
        )

        raw_metadata = {
            "yt_dlp": extraction.raw_info,
            "gemini_response": extraction.raw_gemini_response,
        }

        try:
            saved_reel = await self.saved_reel_repo.create(
                SavedReelCreate(
                    platform=platform,
                    reel_url=normalized_url, # Store normalized
                    status=ReelStatus.processed,
                    title=extraction.metadata.title,
                    description=extraction.metadata.description,
                    raw_metadata=raw_metadata,
                    thumbnail_url=extraction.metadata.thumbnail_url,
                    ai_confidence=verified.score,
                    ai_reasoning=None,
                    ai_model_used=extraction.model_choice.model_name,
                    is_verified_truth=True,
                    media_storage_path=stored_path, # Persist the stored path
                    place_id=place.id,
                )
            )
        except IntegrityError:
            # This reel was already processed (duplicate request or race condition)
            # Retrieve the existing one and return it
            existing_reel = await self.saved_reel_repo.get_by_platform_and_url(platform, normalized_url)
            if existing_reel and existing_reel.place:
                return IngestionResult(
                    saved_reel_id=existing_reel.id,
                    place_id=existing_reel.place.id,
                    verified_place=verified,
                    model_used=existing_reel.ai_model_used or extraction.model_choice.model_name,
                )
            # If we can't find it, something is seriously wrong
            raise

        return IngestionResult(
            saved_reel_id=saved_reel.id,
            place_id=place.id,
            verified_place=verified,
            model_used=extraction.model_choice.model_name,
        )
    

    @staticmethod
    def build_text_blob(*parts: str | None) -> str:
        cleaned = [part.strip() for part in parts if part and part.strip()]
        return " ".join(cleaned)
