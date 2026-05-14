from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

class Settings(BaseSettings):
    host: str = '0.0.0.0'
    port: int = 8000

    location: str = "Sint-Martens-Latem, Belgium"
    timezone: str = "Europe/Brussels"
    
    model_file: Path = PROJECT_ROOT / 'model_artifacts/xgboost_model.onnx'
    upload_storage_dir: Path = PROJECT_ROOT / 'storage/uploads'
    
    redis_host: str = 'redis'
    redis_port: int = 6379

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
