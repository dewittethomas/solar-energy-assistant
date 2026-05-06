from repositories.weather_repository import WeatherRepository
from typing import List, Dict, Any

class WeatherService:
    def __init__(self):
        self.repository = WeatherRepository()
    
    def get_weather_forecast(self, latitude: float, longitude: float, timezone: str, 
                           start_date: str, end_date: str) -> Dict[str, Any]:
        return self.repository.fetch_forecast_data(latitude, longitude, timezone, start_date, end_date)