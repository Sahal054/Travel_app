from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from app.services.gemini_location_extractor import (
    GeminiLocationExtractor,
    LocationCandidate,
    LocationExtractionResult,
)
from app.services.model_router import ModelChoice, ModelRouter
from app.services.reel_extractor import ReelDownloadResult, ReelMetadata, YtDlpReelExtractor


@dataclass(frozen=True)
class ReelExtractionResult:
    reel_url: str
    metadata: ReelMetadata
    model_choice: ModelChoice
    candidates: list[LocationCandidate]
    raw_info: dict
    raw_gemini_response: str


class ExtractionPipeline:
    def __init__(
        self,
        *,
        reel_extractor: YtDlpReelExtractor | None = None,
        location_extractor: GeminiLocationExtractor | None = None,
        model_router: ModelRouter | None = None,
    ) -> None:
        self.reel_extractor = reel_extractor or YtDlpReelExtractor()
        self.location_extractor = location_extractor or GeminiLocationExtractor()
        self.model_router = model_router or ModelRouter()

    async def extract(
        self,
        *,
        reel_url: str,
        prefer_high_accuracy: bool = False,
    ) -> ReelExtractionResult:
        with TemporaryDirectory() as tmp_dir:
            download = await self.reel_extractor.download(reel_url, Path(tmp_dir))
            text_blob = self._build_text_blob(download.metadata)
            model_choice = self.model_router.select_model(
                text_blob, prefer_high_accuracy=prefer_high_accuracy
            )
            location_result = await self.location_extractor.extract_candidates(
                model_name=model_choice.model_name,
                video_path=download.video_path,
                metadata_text=text_blob,
            )

        return ReelExtractionResult(
            reel_url=reel_url,
            metadata=download.metadata,
            model_choice=model_choice,
            candidates=location_result.candidates,
            raw_info=download.raw_info,
            raw_gemini_response=location_result.raw_response,
        )

    @staticmethod
    def _build_text_blob(metadata: ReelMetadata) -> str:
        tag_text = " ".join(metadata.tags)
        caption_text = " ".join(metadata.captions)
        parts = [metadata.title, metadata.description, tag_text, caption_text]
        cleaned = [part.strip() for part in parts if part and part.strip()]
        return " ".join(cleaned)
