"""yt-dlp based provider for YouTube / YouTube Music audio download.

Runs yt-dlp as a subprocess and streams progress by parsing the
`--progress-template` output (percent is computed from
downloaded/total bytes because yt-dlp 2026 may report percent as NA).
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from downtube.config import settings
from downtube.providers.base import ProgressCallback


def _ffmpeg_args() -> list[str]:
    path = settings.ffmpeg_path
    if path and path not in ("ffmpeg", ""):
        directory = os.path.dirname(path)
        if directory:
            return ["--ffmpeg-location", directory]
    return []


class YtdlpProvider:
    name = "ytdlp"

    def can_handle(self, url: str) -> bool:
        """Check if URL is a YouTube video."""
        return "youtube.com" in url or "youtu.be" in url

    async def search(self, query: str, limit: int = 20) -> list[dict]:
        """Search YouTube via yt-dlp (ytsearch:)."""
        search_query = f"ytsearch{limit}:{query}"
        cmd = self._base_cmd() + [
            "--dump-json",
            "--no-download",
            "--no-warnings",
            "--flat-playlist",
            search_query,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, err = await proc.communicate()
        text = out.decode(errors="ignore")

        results = []
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    info = json.loads(line)
                    vid = info.get("id", "")
                    results.append({
                        "id": vid,
                        "title": info.get("title") or "untitled",
                        "artist": info.get("artist") or info.get("uploader"),
                        "duration": info.get("duration"),
                        "type": "song",
                        "url": f"https://www.youtube.com/watch?v={vid}" if vid else "",
                        "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else None,
                        "year": str(info.get("upload_date", ""))[:4] if info.get("upload_date") else None,
                    })
                except json.JSONDecodeError:
                    continue
        return results

    @staticmethod
    def _base_cmd() -> list[str]:
        # Use the interpreter's yt_dlp module so we don't depend on yt-dlp
        # being on PATH.
        return [sys.executable, "-m", "yt_dlp"]

    async def resolve(self, url: str) -> "object":
        from downtube.providers.base import ResolveResult
        from downtube.providers.router import classify

        info = await self.get_info(url)
        return ResolveResult(
            url=url,
            provider="ytdlp",
            source_id=info.get("id", ""),
            kind=classify(url),
            title=info.get("title"),
        )

    async def get_info(self, url: str) -> dict:
        cmd = self._base_cmd() + [
            "--dump-json",
            "--no-download",
            "--no-warnings",
            "--ignore-errors",
            url,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, err = await proc.communicate()
        text = out.decode(errors="ignore")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        raise RuntimeError("yt-dlp returned no info: " + err.decode(errors="ignore")[:300])

    def download(
        self,
        url: str,
        out_path: Path,
        audio_format: str,
        on_progress: ProgressCallback,
    ) -> str:
        """Download `url` to `out_path.<ext>` and return the final file path.

        `on_progress(percent, phase)` is called from the worker thread.
        """
        out_template = f"{out_path}.%(ext)s"
        cmd = self._base_cmd() + [
            "-f",
            "bestaudio",
            "-x",
            "--audio-format",
            audio_format,
            "--no-keep-video",
            "--newline",
            "--no-warnings",
            "--progress-template",
            "PROGRESS %(progress.downloaded_bytes)s %(progress.total_bytes)s",
            *_ffmpeg_args(),
            "-o",
            out_template,
            url,
        ]

        final_path: str | None = None
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        for raw in proc.stdout:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("PROGRESS "):
                parts = line[len("PROGRESS ") :].split()
                downloaded = _to_float(parts[0]) if parts else None
                total = _to_float(parts[1]) if len(parts) > 1 else None
                percent = None
                if downloaded is not None and total:
                    percent = min(100.0, downloaded / total * 100.0)
                on_progress(percent, "downloading")
            elif "Destination:" in line:
                final_path = line.split("Destination:", 1)[1].strip()
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"yt-dlp exited with code {proc.returncode}")

        if final_path:
            return final_path
        guess = Path(f"{out_path}.{audio_format}")
        if guess.exists():
            return str(guess)
        raise RuntimeError("yt-dlp finished but output file not found")


def _to_float(value: str) -> float | None:
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def is_youtube(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url


def is_youtube_music(url: str) -> bool:
    return "music.youtube.com" in url
