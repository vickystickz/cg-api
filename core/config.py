from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Campus Guide API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "Development"
    ROOT_PATH: str = ""
    API_V1_STR: str = "/api/v1"

    ALLOWED_ORIGINS: str = "*"

    DATABASE_URL: str          # Required — will error if missing from .env

    SECRET_KEY: str            # Required
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
