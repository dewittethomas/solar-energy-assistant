import requests
from typing import Dict, Any

HOURLY_PARAMS = [
    'temperature_2m',
    'wind_direction_10m',
    'wind_speed_10m',
    'cloud_cover',
    'shortwave_radiation',
    'diffuse_radiation',
    'direct_normal_irradiance',
    'terrestrial_radiation'
]

class WeatherRepository:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
    
    def fetch_forecast_data(self, latitude: float, longitude: float, timezone: str, 
                          start_date: str, end_date: str) -> Dict[str, Any]:
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'hourly': HOURLY_PARAMS,
            'timezone': timezone,
            'start_date': start_date,
            'end_date': end_date
        }
            
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch weather data: {str(e)}")