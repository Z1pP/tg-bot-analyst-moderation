import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = os.path.join(BASE_DIR, ".env")


class AlembicConfig(BaseSettings):
    DEV_DB_URL_FOR_ALEMBIC: str = Field(alias="DEV_DB_URL_FOR_ALEMBIC")
    PROD_DB_URL_FOR_ALEMBIC: str = Field(alias="PROD_DB_URL_FOR_ALEMBIC")

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        extra = "allow"


class DataBaseConfig(BaseSettings):
    DEV_DATABASE_URL: str = Field(alias="DEV_DATABASE_URL")
    PROD_DATABSE_URL: str = Field(alias="PROD_DATABSE_URL")

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        extra = "allow"


class Settings(BaseSettings):
    BOT_TOKEN: str = Field(alias="BOT_TOKEN")
    IS_DEVELOPMENT: bool = Field(alias="IS_DEVELOPMENT", default=False)

    @property
    def ALEMBIC_DB_URL(self) -> str:
        alembic_config = AlembicConfig()

        if self.IS_DEVELOPMENT:
            return alembic_config.DEV_DB_URL_FOR_ALEMBIC
        return alembic_config.PROD_DB_URL_FOR_ALEMBIC

    @property
    def DATABASE_URL(self) -> str:
        db_config = DataBaseConfig()

        if self.IS_DEVELOPMENT:
            return db_config.DEV_DATABASE_URL
        return db_config.PROD_DATABSE_URL

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()
