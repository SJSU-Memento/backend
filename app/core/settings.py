from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import computed_field

class Settings(BaseSettings):
    env: Literal['production'] | Literal['development'] = "production"
    database_url: str
    openai_api_key: str

    @computed_field
    @property
    def database_url_async(self) -> str:
        # some cloud providers use the "postgres://" or "postgresql://" prefix
        # we're using asyncpg so we need to use postgresql+asyncpg://
        return self.database_url.replace(
            "postgres://",
            "postgresql+asyncpg://"
        ).replace(
            "postgresql://",
            "postgresql+asyncpg://"
        )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()