from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment / .env.

    Field names match the documented environment variables (case-insensitive).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    music_root: Path = Path("./music")
    data_dir: Path = Path("./data")
    database_url: str = "sqlite+aiosqlite:///./data/downtube.db"
    download_concurrency: int = 2
    ytdlp_path: str = "yt-dlp"
    ffmpeg_path: str = "ffmpeg"
    default_format: str = "mp3"
    default_quality: str = "best"
    log_level: str = "info"

    @property
    def frontend_dist(self) -> Path:
        """Absolute path to the built SPA (frontend/dist).

        config.py lives at <repo>/backend/src/downtube/config.py, so the repo
        root is four levels up; the SPA is built to <repo>/frontend/dist.
        """
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        return (repo_root / "frontend" / "dist").resolve()

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.music_root.mkdir(parents=True, exist_ok=True)


settings = Settings()
