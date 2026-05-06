from core.settings import get_settings
import redis
from typing import Any, Optional

class CacheRepository:
    def __init__(self):
        settings = get_settings()

        try:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        except Exception:
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        if not self.client:
            return None

        try:
            return self.client.get(key)
        except Exception:
            return None

    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        if not self.client:
            return False

        try:
            self.client.setex(key, expire, value)
            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        if not self.client:
            return False

        try:
            self.client.delete(key)
            return True
        except Exception:
            return False