from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2 import WKTElement

from app.models.place import Place
from app.models.saved_reel import ReelStatus, SavedReel
from app.repositories.interfaces import (
    PlaceCandidate,
    PlaceRepository,
    SavedReelCreate,
    SavedReelRepository,
)


class SqlAlchemyPlaceRepository(PlaceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_google_place_id(self, google_place_id: str) -> Place | None:
        stmt = select(Place).where(Place.google_place_id == google_place_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: PlaceCandidate) -> Place:
        point = WKTElement(f"POINT({data.longitude} {data.latitude})", srid=4326)
        place = Place(
            google_place_id=data.google_place_id,
            place_name=data.place_name,
            formatted_address=data.formatted_address,
            city=data.city,
            region=data.region,
            country=data.country,
            location=point,
        )
        self.session.add(place)
        await self.session.commit()
        await self.session.refresh(place)
        return place

    async def get_or_create(self, data: PlaceCandidate) -> Place:
        existing = await self.get_by_google_place_id(data.google_place_id)
        if existing:
            return existing

        try:
            return await self.create(data)
        except IntegrityError:
            await self.session.rollback()
            existing = await self.get_by_google_place_id(data.google_place_id)
            if existing:
                return existing
            raise


class SqlAlchemySavedReelRepository(SavedReelRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_platform_and_url(
        self, platform: str, reel_url: str
    ) -> SavedReel | None:
        stmt = select(SavedReel).where(
            SavedReel.platform == platform,
            SavedReel.reel_url == reel_url,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: SavedReelCreate) -> SavedReel:
        saved_reel = SavedReel(
            platform=data.platform,
            reel_url=data.reel_url,
            status=data.status,
            title=data.title,
            description=data.description,
            raw_metadata=data.raw_metadata,
            thumbnail_url=data.thumbnail_url,
            ai_confidence=data.ai_confidence,
            ai_reasoning=data.ai_reasoning,
            ai_model_used=data.ai_model_used,
            is_verified_truth=data.is_verified_truth,
            media_storage_path=data.media_storage_path,
            place_id=data.place_id,
            user_id=data.user_id,
        )
        self.session.add(saved_reel)
        await self.session.commit()
        await self.session.refresh(saved_reel)
        return saved_reel

    async def update_status(self, saved_reel_id: int, status: ReelStatus) -> SavedReel:
        stmt = select(SavedReel).where(SavedReel.id == saved_reel_id)
        result = await self.session.execute(stmt)
        saved_reel = result.scalar_one()
        saved_reel.status = status
        await self.session.commit()
        await self.session.refresh(saved_reel)
        return saved_reel