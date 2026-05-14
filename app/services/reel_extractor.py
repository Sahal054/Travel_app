from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL
from typing import cast


@dataclass(frozen=True)
class ReelMetadata:
    title: str | None
    description: str | None
    tags: list[str]
    captions: list[str]
    thumbnail_url: str | None
    source_url: str | None
    platform: str | None


@dataclass(frozen=True)
class ReelDownloadResult:
    video_path: Path
    metadata: ReelMetadata
    raw_info: dict[str, Any]


class YtDlpReelExtractor:
    def __init__(
        self,
        *,
        subtitles_languages: list[str] | None = None,
        video_format: str = "mp4/best",
    ) -> None:
        self.subtitles_languages = subtitles_languages or ["en", "ml"]
        self.video_format = video_format

    async def download(self, reel_url: str, temp_dir: Path) -> ReelDownloadResult:
        return await asyncio.to_thread(self._download_sync, reel_url, temp_dir)

    def _download_sync(self, reel_url: str, temp_dir: Path) -> ReelDownloadResult:
        ydl_opts = {
            "outtmpl": str(temp_dir / "%(id)s.%(ext)s"),
            "format": self.video_format,
            "merge_output_format": "mp4",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": self.subtitles_languages,
            "subtitlesformat": "vtt",
        }

        with YoutubeDL(cast(Any, ydl_opts)) as ydl:
            info = ydl.extract_info(reel_url, download=True)
            video_path = self._resolve_video_path(cast(dict[str, Any], info), ydl, temp_dir)

        captions = self._load_captions(temp_dir)
        metadata = ReelMetadata(
            title=info.get("title"),
            description=info.get("description"),
            tags=info.get("tags") or [],
            captions=captions,
            thumbnail_url=info.get("thumbnail"),
            source_url=info.get("webpage_url") or reel_url,
            platform=info.get("extractor_key") or info.get("extractor"),
        )

        return ReelDownloadResult(
            video_path=video_path,
            metadata=metadata,
            raw_info=dict(info),
        )

    @staticmethod
    def _resolve_video_path(info: dict[str, Any], ydl: YoutubeDL, temp_dir: Path) -> Path:
        filename = info.get("_filename")
        if filename:
            path = Path(filename)
            if path.exists():
                return path

        requested = info.get("requested_downloads")
        if requested:
            candidate = requested[0].get("filepath") or requested[0].get("filename")
            if candidate:
                path = Path(candidate)
                if path.exists():
                    return path

        prepared = ydl.prepare_filename(cast(Any, info))
        path = Path(prepared)
        if path.exists():
            return path
        matches = sorted(temp_dir.glob("*"))
        if not matches:
            raise FileNotFoundError("No downloaded media file found")

        video_exts = {".mp4", ".mkv", ".mov", ".webm", ".m4v"}
        for match in matches:
            if match.suffix.lower() in video_exts:
                return match

        # Fallback to first file if no known video extension is present
        return matches[0]

    def _load_captions(self, temp_dir: Path) -> list[str]:
        captions: list[str] = []
        for vtt_path in temp_dir.glob("*.vtt"):
            captions.extend(self._parse_vtt(vtt_path.read_text(errors="ignore")))
        return captions

    @staticmethod
    def _parse_vtt(content: str) -> list[str]:
        lines: list[str] = []
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("WEBVTT"):
                continue
            if "-->" in line:
                continue
            if line.isdigit():
                continue
            lines.append(line)
        return lines
