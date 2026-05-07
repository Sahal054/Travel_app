from dataclasses import dataclass

from typing import Protocol

from app.models.place import Place

from app.models.saved_reel import ReelStatus, SavedReel



@dataclass(frozen= True)
class PlaceCandidate:
    google_place_id: str
    place_name: str
    latitude: float
    longitude: float
    formatted_address: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None

@dataclass(frozen=True)
class SavedReelCreate:
    platform: str
    reel_url: str
    status: ReelStatus = ReelStatus.queued
    title: str | None = None
    description: str | None = None
    raw_metadata: dict | None = None
    thumbnail_url: str | None = None
    ai_confidence: float | None = None
    ai_reasoning: str | None = None
    ai_model_used: str | None = None
    is_verified_truth: bool = False
    media_storage_path: str | None = None
    place_id: int | None = None
    user_id: int | None = None

class PlaceRepository(Protocol):
    async def get_by_google_place_id(self,google_place_id :str) -> Place |None:...

    async def create(self,data: PlaceCandidate) -> Place:...

    async def get_or_create(self, data: PlaceCandidate) -> Place: ...


class SavedReelRepository(Protocol):
    async def get_by_platform_and_url (self, platform:str , reel_url:str ) -> SavedReel | None:...

    async def create(self, data: SavedReelCreate) -> SavedReel: ...

    async def update_status(self, saved_reel_id: int, status: ReelStatus) -> SavedReel: ...