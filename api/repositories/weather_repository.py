import requests

from models.model_features import WEATHER_COLUMNS

class WeatherRepository:
    def __init__(self) -> None:
        self.forecast_url = 'https://api.open-meteo.com/v1/forecast'
        self.archive_url = 'https://archive-api.open-meteo.com/v1/archive'

    def fetch_forecast_data(
        self,
        latitude: float,
        longitude: float,
        timezone: str,
        start_date: str,
        end_date: str
    ) -> dict[str, object]:
        return self._fetch_weather_data(
            self.forecast_url,
            latitude,
            longitude,
            timezone,
            start_date,
            end_date
        )

    def fetch_historical_data(
        self,
        latitude: float,
        longitude: float,
        timezone: str,
        start_date: str,
        end_date: str
    ) -> dict[str, object]:
        return self._fetch_weather_data(
            self.archive_url,
            latitude,
            longitude,
            timezone,
            start_date,
            end_date
        )

    def _fetch_weather_data(
        self,
        url: str,
        latitude: float,
        longitude: float,
        timezone: str,
        start_date: str,
        end_date: str
    ) -> dict[str, object]:
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'hourly': WEATHER_COLUMNS,
            'timezone': timezone,
            'start_date': start_date,
            'end_date': end_date
        }

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f'Failed to fetch weather data: {str(exc)}'
            ) from exc
