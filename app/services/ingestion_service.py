from dataclasses import dataclass

from app.services.model_router import ModelChoice, ModelRouter
from app.repositories import PlaceRepository, SavedReelRepository


@dataclass(frozen=True)
class IngestionPlan:
    reel_url: str
    model_choice: ModelChoice


class IngestionService:
    def __init__(
        self,
        *,
        place_repo: PlaceRepository,
        saved_reel_repo: SavedReelRepository,
        model_router: ModelRouter | None = None,
    ) -> None:
        self.place_repo = place_repo
        self.saved_reel_repo = saved_reel_repo
        self.model_router = model_router or ModelRouter()

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
    def build_text_blob(*parts: str | None) -> str:
        cleaned = [part.strip() for part in parts if part and part.strip()]
        return " ".join(cleaned)
