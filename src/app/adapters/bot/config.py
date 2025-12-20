from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class BotConfig(BaseSettings):
    BOT_TOKEN: str = Field(alias="BOT_TOKEN")
    IS_DEVELOPMENT: bool = Field(False, alias="IS_DEVELOPMENT")
    TIMEZONE: str = Field(
        "Europe/Moscow", alias="TIMEZONE", description="Default timezone "
    )
    REDIS_URL: str = Field(alias="REDIS_URL")
    STATIC_URL: str = Field(alias="STATIC_URL")

    # Сервисный вызов backend
    BACKEND_URL: str = Field(alias="BACKEND_URL")
    SERVICE_BOT_PRIVATE_KEY_PATH: str = Field(alias="SERVICE_BOT_PRIVATE_KEY_PATH")
    SERVICE_JWT_AUDIENCE: str = Field("backend", alias="SERVICE_JWT_AUDIENCE")
    SERVICE_JWT_TTL_SECONDS: int = Field(300, alias="SERVICE_JWT_TTL_SECONDS")

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"


try:
    bot_config = BotConfig()
except Exception as e:
    raise RuntimeError(f"Ошибка загрузки конфигурации: {e}") from e
