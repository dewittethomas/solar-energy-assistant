from repositories.cache_repository import CacheRepository

class CacheService:
    def __init__(self, repository: CacheRepository) -> None:
        self.repository = repository

    def get(self, key: str) -> str | None:
        return self.repository.get(key)

    def set(self, key: str, value: str, expire: int = 3600) -> bool:
        return self.repository.set(key, value, expire)

    def delete(self, key: str) -> bool:
        return self.repository.delete(key)
