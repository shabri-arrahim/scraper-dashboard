import datetime

from pathlib import Path
from typing import Optional, Annotated, List, Any, Literal
from pydantic_settings import BaseSettings
from pydantic import AnyUrl, BeforeValidator, model_validator


def parse_config_field(value: Any) -> list[str] | str:
    if isinstance(value, str) and not value.startswith("["):
        return [item.strip() for item in value.split(",")]
    elif isinstance(value, list | str):
        return value
    raise ValueError(f"Invalid Field: {value}")


class Settings(BaseSettings):
    TIME_NOW = lambda _: datetime.datetime.now(datetime.timezone.utc).astimezone()

    API_TOKEN: str
    ALLOWED_HOSTS: Annotated[List[str] | str, BeforeValidator(parse_config_field)] = []
    CORS_ORIGINS: Annotated[List[AnyUrl] | str, BeforeValidator(parse_config_field)] = (
        []
    )
    RATE_LIMIT: int  # Requests per minute

    # DIRECTORY CONFIGURATIONS
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    SOURCE_DIR: Path = BASE_DIR / "sources"
    SCRIPTS_DIR: Path = SOURCE_DIR / "scripts"
    DOWNLOAD_DIR: Path = SOURCE_DIR / "downloads"
    SCRIPTS_ASSETS_DIR: Path = SCRIPTS_DIR / "assets"
    LOGS_DIR: Path = SOURCE_DIR / "logs"

    def _check_if_the_path_exist_or_create(self, path: Path) -> None:
        if path.exists():
            pass
        else:
            import os

            os.makedirs(path)

    @model_validator(mode="after")
    def check_dir(self) -> None:
        for path in [
            self.SOURCE_DIR,
            self.SCRIPTS_DIR,
            self.SCRIPTS_ASSETS_DIR,
            self.DOWNLOAD_DIR,
            self.LOGS_DIR,
        ]:
            self._check_if_the_path_exist_or_create(path)
        return self

    # DATABASE CONFIGURATION
    DATABASE_URL: str = f"sqlite:///{SOURCE_DIR}/data.db"

    # TELEGRAM CONFIGURATION
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_MAX_MESSAGE_CHAR: int = 4090

    # CELERY CONFIGURATION
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    # === Core Worker Settings ===
    CELERY_WORKER_CONCURRENCY: int = 3  # 3 workers max
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1  # One task per worker
    CELERY_TASK_ACKS_LATE: bool = False  # Acknowledge immediately to prevent duplicates
    # === Memory Management ===
    CELERY_WORKER_MAX_MEMORY_PER_CHILD: int = (
        1000000  # 1GB per worker (kill if exceeded)
    )
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = (
        10  # Restart after 10 tasks for memory cleanup
    )
    # === Timeouts For 24-Hour Tasks ===
    CELERY_TASK_SOFT_TIME_LIMIT: int = 25 * 60 * 60  # 25 hours (25 * 60 * 60)
    CELERY_TASK_TIME_LIMIT: int = 26 * 60 * 60  # 26 hours (hard limit)
    CELERY_TASK_REJECT_ON_WORKER_LOST: int = True
    # === Results Backend ===
    CELERY_RESULT_EXPIRES: int = 48 * 60 * 60  # 48 hours

    # SECURITY HEADERS
    SECURITY_HEADERS: dict = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": (
            "default-src 'self' cdn.tailwindcss.com unpkg.com cdnjs.cloudflare.com;"
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.tailwindcss.com unpkg.com;"
            "style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com;"
            "font-src 'self' cdnjs.cloudflare.com;"
            "img-src 'self' data:;"
            "connect-src 'self' https://scraper-dash.ninoproject.my.id;"
        ),
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    # ENVIRONMENT SETTINGS
    ENVIRONMENT: Literal["local", "development", "production"] = "local"
    DEBUG: bool = "true" in ["on", "1", "true"]
    MAX_LOG_LINES: int = 1000

    class Config:
        env_file = ".env"


settings = Settings()
