from repositories.weather_repository import WeatherRepository
from typing import List, Dict, Any

class WeatherService:
    def __init__(self):
        self.repository = WeatherRepository()
    
    def get_weather_forecast(self, latitude: float, longitude: float, timezone: str) -> Dict[str, Any]:
        """
        Get weather forecast for a given location.
        
        Args:
            latitude (float): Latitude of the location
            longitude (float): Longitude of the location
            timezone (str): Timezone for the location
            
        Returns:
            Dict[str, Any]: Weather forecast data
        """
        return self.repository.fetch_forecast_data(latitude, longitude, timezone)