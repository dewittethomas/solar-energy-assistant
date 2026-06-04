import time

import requests

from models.model_features import WEATHER_COLUMNS

class WeatherRepository:
    def __init__(self) -> None:
        self.forecast_url = 'https://api.open-meteo.com/v1/forecast'
        self.archive_url = 'https://archive-api.open-meteo.com/v1/archive'
        self._cache: dict[tuple[object, ...], dict[str, object]] = {}
        self._forecast_cache_ttl_seconds = 15 * 60
        self._historical_cache_ttl_seconds = 24 * 60 * 60

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
            end_date,
            self._forecast_cache_ttl_seconds,
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
            end_date,
            self._historical_cache_ttl_seconds,
        )

    def _fetch_weather_data(
        self,
        url: str,
        latitude: float,
        longitude: float,
        timezone: str,
        start_date: str,
        end_date: str,
        ttl_seconds: int,
    ) -> dict[str, object]:
        cache_key = (
            url,
            round(latitude, 4),
            round(longitude, 4),
            timezone,
            start_date,
            end_date,
        )
        cached = self._read_cache(cache_key, ttl_seconds)

        if cached is not None:
            return cached

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
            payload = response.json()
            self._cache[cache_key] = {
                'cached_at': time.time(),
                'payload': payload,
            }
            return payload
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f'Failed to fetch weather data: {str(exc)}'
            ) from exc

    def _read_cache(
        self,
        cache_key: tuple[object, ...],
        ttl_seconds: int,
    ) -> dict[str, object] | None:
        entry = self._cache.get(cache_key)

        if not entry:
            return None

        now = time.time()

        if now - float(entry['cached_at']) > ttl_seconds:
            self._cache.pop(cache_key, None)
            return None

        return entry['payload']  # type: ignore[return-value]
