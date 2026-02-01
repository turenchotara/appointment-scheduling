from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    All settings can be configured via environment variables or a .env file.
    """
    
    # Data paths
    FAQ_DATA_PATH: str = ""
    DB_PATH: str = ""
    COLLECTION_NAME: str = ""
    SCHEDULE_FILE_PATH: str = ""
    
    # Cal.com API settings
    API_KEY: str = ""
    
    # Azure OpenAI settings
    AZURE_ENDPOINT: str = ""
    AZURE_DEPLOYMENT: str = "gpt-4.1"
    AZURE_API_KEY: str = ""
    AZURE_API_VERSION: str = ""
    
    # Google Gemini settings
    GOOGLE_API_KEY: str = ""
    
    # Module loading configuration
    BACKEND_MODULES: list[str] = [
        "backend.models",
        "backend.rag",
        "backend.api",
        "backend.agent"
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=False
    )


settings: Settings = Settings()
