from pathlib import Path
from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

class Settings(BaseSettings):
    host: str = '0.0.0.0'
    port: int = 8000

    location: str = "Sint-Martens-Latem, Belgium"
    timezone: str = "Europe/Brussels"

    model_storage_dir: Path = PROJECT_ROOT / 'model_artifacts'
    upload_storage_dir: Path = PROJECT_ROOT / 'storage/uploads'
    minimum_model_r2: float = 0.5

    redis_host: str = 'redis'
    redis_port: int = 6379
    postgres_host: str = '127.0.0.1'
    postgres_port: int = 5432
    postgres_user: str = 'postgres'
    postgres_password: str = 'postgres'
    postgres_db: str = 'solar_energy_assistant'
    adminer_port: int = 8080
    cors_allowed_origins: str = (
        'http://localhost:5173,http://127.0.0.1:5173'
    )

    @property
    def database_url(self) -> str:
        return (
            f'postgresql://{self.postgres_user}:{self.postgres_password}'
            f'@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}'
        )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(',')
            if origin.strip()
        ]

    @field_validator(
        'model_storage_dir',
        'upload_storage_dir',
        mode='after'
    )
    @classmethod
    def resolve_project_path(cls, value: Path) -> Path:
        if value.is_absolute():
            return value

        return PROJECT_ROOT / value

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / '.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
