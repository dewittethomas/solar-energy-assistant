from repositories.geocoding_repository import GeocodingRepository

class GeocodingService:
    def __init__(
        self,
        repository: GeocodingRepository
    ) -> None:
        self.repository = repository

    def get_coordinates(self, location: str) -> dict[str, float] | None:
        return self.repository.geocode_location(location)
