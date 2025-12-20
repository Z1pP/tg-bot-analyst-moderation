from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class ApiConfig(BaseSettings):
    SERVICE_BOT_PUBLIC_KEY_PATH: str = Field(alias="SERVICE_BOT_PUBLIC_KEY_PATH")

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"


try:
    api_config = ApiConfig()
except Exception as e:
    raise RuntimeError(f"Ошибка загрузки конфигурации: {e}") from e
