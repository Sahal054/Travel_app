from __future__ import annotations

import asyncio
import base64
import logging
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LocationCandidate:
    place_name: str
    city: str | None
    region: str | None
    country: str | None
    latitude: float | None
    longitude: float | None
    confidence: float | None
    reasoning: str | None
    source_evidence: list[str]


@dataclass(frozen=True)
class LocationExtractionResult:
    candidates: list[LocationCandidate]
    raw_response: str
    language: str | None
    model_used: str


class _GeminiCandidateSchema(BaseModel):
    place_name: str
    city: str | None = None
    region: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    reasoning: str | None = None
    source_evidence: list[str] = Field(default_factory=list)


class _GeminiLocationSchema(BaseModel):
    language: str | None = None
    candidates: list[_GeminiCandidateSchema] = Field(default_factory=list)


class GeminiLocationExtractor:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        max_media_bytes: int = 25 * 1024 * 1024,
        enable_search_grounding: bool = True,
        client: Any | None = None,
    ) -> None:
        resolved_key = api_key or settings.gemini_api_key
        if client is None and not resolved_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        self.client = client or genai.Client(api_key=resolved_key)
        self.max_media_bytes = max_media_bytes
        self.enable_search_grounding = enable_search_grounding

    async def extract_candidates(
        self,
        *,
        model_name: str,
        video_path: Path,
        metadata_text: str,
    ) -> LocationExtractionResult:
        return await asyncio.to_thread(
            self._extract_candidates_sync,
            model_name,
            video_path,
            metadata_text,
        )

    def _extract_candidates_sync(
        self,
        model_name: str,
        video_path: Path,
        metadata_text: str,
    ) -> LocationExtractionResult:
        prompt = self._build_prompt(metadata_text)
        contents = self._build_contents(prompt, video_path)

        media_bytes = video_path.stat().st_size if video_path.exists() else None
        media_included = (
            video_path.exists()
            and media_bytes is not None
            and media_bytes <= self.max_media_bytes
        )
        logger.info(
            "gemini_request",
            extra={
                "event": "gemini_request",
                "model_name": model_name,
                "grounding_enabled": self.enable_search_grounding,
                "media_included": media_included,
                "media_bytes": media_bytes,
            },
        )

        tools = [types.Tool(google_search=types.GoogleSearch())] if self.enable_search_grounding else None
        config = types.GenerateContentConfig(
            temperature=0.2,
            tools=tools,
        )
        response = self.client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )

        raw_text = self._get_response_text(response)
        schema = self._parse_response(raw_text)
        logger.info(
            "gemini_response",
            extra={
                "event": "gemini_response",
                "model_name": model_name,
                "language": schema.language,
                "candidate_count": len(schema.candidates),
            },
        )
        candidates = [
            LocationCandidate(
                place_name=item.place_name,
                city=item.city,
                region=item.region,
                country=item.country,
                latitude=item.latitude,
                longitude=item.longitude,
                confidence=item.confidence,
                reasoning=item.reasoning,
                source_evidence=item.source_evidence,
            )
            for item in schema.candidates
        ]

        return LocationExtractionResult(
            candidates=candidates,
            raw_response=raw_text,
            language=schema.language,
            model_used=model_name,
        )

    @staticmethod
    def _build_prompt(metadata_text: str) -> str:
        return (
            "You are a location extraction system. Analyze the reel video, audio, and text "
            "to identify location candidates (business names, landmarks, natural viewpoints). "
            "The input text may be Malayalam or English. Use Google Search Grounding when possible.\n\n"
            "Return JSON only in this schema:\n"
            "{\n"
            "  \"language\": \"<detected language or null>\",\n"
            "  \"candidates\": [\n"
            "    {\n"
            "      \"place_name\": \"...\",\n"
            "      \"city\": \"...\",\n"
            "      \"region\": \"...\",\n"
            "      \"country\": \"...\",\n"
            "      \"latitude\": 0.0,\n"
            "      \"longitude\": 0.0,\n"
            "      \"confidence\": 0.0,\n"
            "      \"reasoning\": \"...\",\n"
            "      \"source_evidence\": [\"text\", \"audio\", \"visual\"]\n"
            "    }\n"
            "  ]\n"
            "}\n\n"
            f"Metadata text:\n{metadata_text}"
        )

    def _build_contents(self, prompt: str, video_path: Path) -> list[dict[str, Any]]:
        mime_type = mimetypes.guess_type(video_path.name)[0] or "video/mp4"
        parts: list[dict[str, Any]] = [{"text": prompt}]

        if video_path.exists() and video_path.stat().st_size <= self.max_media_bytes:
            data = video_path.read_bytes()
            encoded = base64.b64encode(data).decode("ascii")
            parts.append(
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": encoded,
                    }
                }
            )

        return [{"role": "user", "parts": parts}]

    @staticmethod
    def _get_response_text(response: Any) -> str:
        text = getattr(response, "text", None)
        if text:
            return text

        candidates = getattr(response, "candidates", None)
        if candidates:
            content = getattr(candidates[0], "content", None)
            parts = getattr(content, "parts", None)
            if parts and hasattr(parts[0], "text"):
                return parts[0].text

        return str(response)

    def _parse_response(self, raw_text: str) -> _GeminiLocationSchema:
        payload = self._extract_json(raw_text)
        try:
            return _GeminiLocationSchema.model_validate_json(payload)
        except ValidationError as exc:
            raise ValueError(f"Invalid Gemini response: {exc}") from exc

    @staticmethod
    def _extract_json(raw_text: str) -> str:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Gemini response does not contain JSON")
        return raw_text[start : end + 1]
