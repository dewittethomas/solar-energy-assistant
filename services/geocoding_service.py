from repositories.geocoding_repository import GeocodingRepository
from typing import Dict, Any, Optional

class GeocodingService:
    def __init__(
            self,
            repository: GeocodingRepository
        ):
        self.repository = repository
    
    def get_coordinates(self, location: str) -> Optional[Dict[str, Any]]:
        
        return self.repository.geocode_location(location)