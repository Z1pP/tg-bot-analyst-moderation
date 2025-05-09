from pydantic import Field
from pydantic_settings import BaseSettings


class DataBaseConfig(BaseSettings):
    DEV_DATABASE_URL: str = Field(alias="DEV_DATABASE_URL")
    PROD_DATABSE_URL: str = Field(alias="PROD_DATABSE_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


class Settings(BaseSettings):
    BOT_TOKEN: str = Field(alias="BOT_TOKEN")
    IS_DEVELOPMENT: bool = Field(alias="IS_DEVELOPMENT", default=False)

    @property
    def DATABASE_URL(self) -> str:
        db_config = DataBaseConfig()

        if self.IS_DEVELOPMENT:
            return db_config.DEV_DATABASE_URL
        return db_config.PROD_DATABSE_URL

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()
