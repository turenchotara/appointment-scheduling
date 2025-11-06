from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    FAQ_DATA_PATH: str = ""
    DB_PATH: str = ""
    COLLECTION_NAME: str = ""
    SCHEDULE_FILE_PATH: str = ""
    BACKEND_MODULES: List[str] = ["backend.models", "backend.rag", "backend.api", "backend.agent"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=False
    )


settings = Settings()
