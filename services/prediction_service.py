from repositories.prediction_repository import PredictionRepository
from services.weather_service import WeatherService
from services.geocoding_service import GeocodingService
from services.cache_service import CacheService
from models.prediction_input import PredictionInput
from models.prediction_output import PredictionOutput
from core.settings import get_settings

from typing import List, Dict, Any
import math
from datetime import datetime


class PredictionService:
    def __init__(
        self,
        weather_service: WeatherService,
        geocoding_service: GeocodingService,
        prediction_repository: PredictionRepository,
        cache_service: CacheService = None
    ):
        self.weather_service = weather_service
        self.geocoding_service = geocoding_service
        self.repository = prediction_repository
        self.cache_service = cache_service

        self.settings = get_settings()

        coords = self.geocoding_service.get_coordinates(self.settings.location)
        if not coords:
            raise ValueError(f"Invalid configured location: {self.settings.location}")

        self.latitude = coords["latitude"]
        self.longitude = coords["longitude"]

    def predict_solar_yield(
        self,
        start_date: str,
        end_date: str
    ) -> List[PredictionOutput]:

        cache_key = (
            f"prediction:"
            f"{round(self.latitude, 5)}:"
            f"{round(self.longitude, 5)}:"
            f"{start_date}:{end_date}"
        )

        if self.cache_service:
            cached = self.cache_service.get(cache_key)
            if cached:
                return cached

        weather_data = self.weather_service.get_weather_forecast(
            self.latitude,
            self.longitude,
            self.settings.timezone,
            start_date,
            end_date
        )

        prediction_inputs, time_data = self._build_inputs(weather_data)

        predictions = self.repository.predict_solar_yield(
            prediction_inputs,
            time_data
        )

        if self.cache_service:
            self.cache_service.set(cache_key, predictions, expire=3600)

        return predictions

    def _build_inputs(self, weather_data: Dict[str, Any]):
        hourly = weather_data.get("hourly", {})

        times = hourly.get("time", [])
        params = self._extract_weather_parameters(hourly)

        self._validate_data_consistency(times, params)

        inputs = []

        for i, t in enumerate(times):
            tf = self._calculate_time_features(t)

            inputs.append(
                PredictionInput(
                    temperature_2m=params["temperature_2m"][i],
                    wind_direction_10m=params["wind_direction_10m"][i],
                    wind_speed_10m=params["wind_speed_10m"][i],
                    cloud_cover=params["cloud_cover"][i],
                    shortwave_radiation=params["shortwave_radiation"][i],
                    diffuse_radiation=params["diffuse_radiation"][i],
                    direct_normal_irradiance=params["direct_normal_irradiance"][i],
                    terrestrial_radiation=params["terrestrial_radiation"][i],
                    hour_sin=tf["hour_sin"],
                    hour_cos=tf["hour_cos"],
                    day_of_year_sin=tf["day_of_year_sin"],
                    day_of_year_cos=tf["day_of_year_cos"]
                )
            )

        return inputs, times

    def _extract_weather_parameters(self, hourly: Dict[str, Any]) -> Dict[str, List]:
        return {
            "temperature_2m": hourly.get("temperature_2m", []),
            "wind_direction_10m": hourly.get("wind_direction_10m", []),
            "wind_speed_10m": hourly.get("wind_speed_10m", []),
            "cloud_cover": hourly.get("cloud_cover", []),
            "shortwave_radiation": hourly.get("shortwave_radiation", []),
            "diffuse_radiation": hourly.get("diffuse_radiation", []),
            "direct_normal_irradiance": hourly.get("direct_normal_irradiance", []),
            "terrestrial_radiation": hourly.get("terrestrial_radiation", [])
        }

    def _validate_data_consistency(self, times: List, params: Dict[str, List]):
        expected_len = len(times)

        for key, values in params.items():
            if len(values) != expected_len:
                raise ValueError(
                    f"Weather data mismatch: {key} has {len(values)} values, expected {expected_len}"
                )

    def _calculate_time_features(self, time_string: str) -> Dict[str, float]:
        dt = datetime.fromisoformat(time_string.replace("Z", "+00:00"))

        hour = dt.hour
        day_of_year = dt.timetuple().tm_yday

        return {
            "hour_sin": math.sin(2 * math.pi * hour / 24),
            "hour_cos": math.cos(2 * math.pi * hour / 24),
            "day_of_year_sin": math.sin(2 * math.pi * day_of_year / 365),
            "day_of_year_cos": math.cos(2 * math.pi * day_of_year / 365)
        }