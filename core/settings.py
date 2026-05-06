from pathlib import Path
from functools import lru_cache
from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    host: str = '0.0.0.0'
    port: int = 8000

    location: str = "Sint-Martens-Latem, Belgium"
    timezone: str = "Europe/Brussels"
    
    model_file: Path = BASE_DIR / 'model_artifacts/xgboost_model.onnx'
    
    redis_host: str = 'redis'
    redis_port: int = 6379

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()