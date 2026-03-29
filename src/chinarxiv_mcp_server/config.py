"""Configuration settings for the ChinaRxiv MCP server."""

import sys
import logging
from pathlib import Path

import httpx
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("chinarxiv-mcp-server")


class Settings(BaseSettings):
    """Server configuration settings."""

    APP_NAME: str = "chinarxiv-mcp-server"
    APP_VERSION: str = "0.1.0"
    API_BASE_URL: str = "https://chinarxiv.org"
    API_EMAIL: str = "olety7@gmail.com"
    MAX_RESULTS: int = 100
    REQUEST_TIMEOUT: int = 30

    model_config = SettingsConfigDict(
        env_prefix="CHINARXIV_",
        extra="allow",
    )

    @property
    def STORAGE_PATH(self) -> Path:
        """Get the resolved storage path and ensure it exists."""
        path = (
            self._get_storage_path_from_args()
            or Path.home() / ".chinarxiv-mcp-server" / "papers"
        )
        path = path.resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _get_storage_path_from_args(self) -> Path | None:
        """Extract storage path from command line arguments."""
        args = sys.argv[1:]
        if len(args) < 2:
            return None
        try:
            idx = args.index("--storage-path")
        except ValueError:
            return None
        if idx + 1 >= len(args):
            return None
        try:
            return Path(args[idx + 1]).resolve()
        except (TypeError, ValueError, OSError) as e:
            logger.warning(f"Invalid storage path: {e}")
            return None


def get_api_client() -> httpx.AsyncClient:
    """Create an httpx client configured for the ChinaRxiv API."""
    settings = Settings()
    headers = {"User-Agent": f"{settings.APP_NAME}/{settings.APP_VERSION}"}
    if settings.API_EMAIL:
        headers["X-API-Email"] = settings.API_EMAIL
    return httpx.AsyncClient(
        base_url=settings.API_BASE_URL,
        timeout=settings.REQUEST_TIMEOUT,
        headers=headers,
    )
