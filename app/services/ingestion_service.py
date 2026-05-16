from dataclasses import dataclass

from app.models.saved_reel import ReelStatus
from app.repositories import PlaceRepository, SavedReelRepository
from app.repositories.interfaces import PlaceCandidate, SavedReelCreate
from app.services.extraction_pipeline import ExtractionPipeline
from app.services.model_router import ModelChoice, ModelRouter
from app.services.places_verifier import GooglePlacesVerifier, VerifiedPlace
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
    


    async def ingest_reel(
        self,
        *,
        reel_url: str,
        prefer_high_accuracy: bool = False,
    ) -> IngestionResult:
        extraction = await self.extraction_pipeline.extract(
            reel_url=reel_url,
            prefer_high_accuracy=prefer_high_accuracy,
        )

        verification = await self.places_verifier.resolve_best(extraction.candidates)
        if not verification.success or not verification.place:
            raise IngestionValidationError(
                verification.error or "Place verification failed"
            )

        verified = verification.place
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

        platform = extraction.metadata.platform or "unknown"

        saved_reel = await self.saved_reel_repo.create(
            SavedReelCreate(
                platform=platform,
                reel_url=extraction.reel_url,
                status=ReelStatus.processed,
                title=extraction.metadata.title,
                description=extraction.metadata.description,
                raw_metadata=raw_metadata,
                thumbnail_url=extraction.metadata.thumbnail_url,
                ai_confidence=verified.score,
                ai_reasoning=None,
                ai_model_used=extraction.model_choice.model_name,
                is_verified_truth=True,
                media_storage_path=None,
                place_id=place.id,
            )
        )

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
