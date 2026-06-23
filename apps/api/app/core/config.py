from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "Novel Forge"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    DATABASE_URL: str = "postgresql+psycopg://novel_forge:change_me@localhost:5432/novel_forge"

    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = "mock-novel-model"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""

    UPLOAD_DIR: str = str(Path(__file__).parent.parent.parent.parent / "data" / "uploads")
    UPLOAD_MAX_SIZE_MB: int = 10
    UPLOAD_ALLOWED_EXTENSIONS: str = ".txt,.md,.markdown"

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
