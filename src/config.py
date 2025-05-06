from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str = Field(alias="BOT_TOKEN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
