from typing import Literal
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    env: Literal['production'] | Literal['development'] = "production"
    database_url: str
    openai_api_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()