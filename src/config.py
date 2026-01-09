from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )

    # Общие настройки
    BOT_TOKEN: str
    IS_DEVELOPMENT: bool = False
    USE_WEBHOOK: bool = (
        False  # True - использовать webhook, False - использовать polling
    )
    TIMEZONE: str = "Europe/Moscow"
    REDIS_URL: str
    SUMMARY_CACHE_TTL_MINUTES: int = 60
    SUMMARY_INVALIDATION_THRESHOLD: int = 50

    # Настройки нейросети
    OPEN_ROUTER_TOKEN: str
    OPEN_ROUTER_MODEL: str = "mistralai/devstral-2512:free"

    # Базы данных
    DEV_DATABASE_URL: str
    PROD_DATABASE_URL: str
    DEV_DB_URL_FOR_ALEMBIC: str
    PROD_DB_URL_FOR_ALEMBIC: str

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """Автоматический выбор URL базы данных."""
        return self.DEV_DATABASE_URL if self.IS_DEVELOPMENT else self.PROD_DATABASE_URL

    @computed_field
    @property
    def ALEMBIC_DB_URL(self) -> str:
        """Автоматический выбор URL для Alembic."""
        return (
            self.DEV_DB_URL_FOR_ALEMBIC
            if self.IS_DEVELOPMENT
            else self.PROD_DB_URL_FOR_ALEMBIC
        )


try:
    settings = Settings()
except Exception as e:
    raise RuntimeError(f"Ошибка загрузки конфигурации:\n{e}") from e
