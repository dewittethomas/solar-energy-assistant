from repositories.cache_repository import CacheRepository

class CacheService:
    def __init__(self, repository: CacheRepository):
        self.repository = repository

    def get(self, key: str):
        return self.repository.get(key)

    def set(self, key: str, value, expire: int = 3600):
        return self.repository.set(key, value, expire)

    def delete(self, key: str):
        return self.repository.delete(key)