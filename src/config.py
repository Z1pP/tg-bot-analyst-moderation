from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class AlembicConfig(BaseSettings):
    DEV_DB_URL_FOR_ALEMBIC: str = Field(alias="DEV_DB_URL_FOR_ALEMBIC")
    PROD_DB_URL_FOR_ALEMBIC: str = Field(alias="PROD_DB_URL_FOR_ALEMBIC")

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"


class DataBaseConfig(BaseSettings):
    DEV_DATABASE_URL: str = Field(alias="DEV_DATABASE_URL")
    PROD_DATABASE_URL: str = Field(alias="PROD_DATABASE_URL")

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"


class Settings(BaseSettings):
    BOT_TOKEN: str = Field(alias="BOT_TOKEN")
    IS_DEVELOPMENT: bool = Field(False, alias="IS_DEVELOPMENT")

    # Используем строку вместо списка для начального чтения
    ADMINS_LIST_STR: str = Field("", alias="ADMINS_LIST_STR")

    @property
    def ADMINS_LIST(self) -> List[str]:
        """Получает список администраторов."""
        if not self.ADMINS_LIST_STR:
            return []
        return [username.strip() for username in self.ADMINS_LIST_STR.split(",")]

    @property
    def ALEMBIC_DB_URL(self) -> str:
        """Получает URL для Alembic в зависимости от режима."""
        alembic_config = AlembicConfig()
        return (
            alembic_config.DEV_DB_URL_FOR_ALEMBIC
            if self.IS_DEVELOPMENT
            else alembic_config.PROD_DB_URL_FOR_ALEMBIC
        )

    @property
    def DATABASE_URL(self) -> str:
        """Получает URL базы данных в зависимости от режима."""
        db_config = DataBaseConfig()
        return (
            db_config.DEV_DATABASE_URL
            if self.IS_DEVELOPMENT
            else db_config.PROD_DATABASE_URL
        )

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"


try:
    settings = Settings()
except Exception as e:
    raise RuntimeError(f"Ошибка загрузки конфигурации: {e}") from e
