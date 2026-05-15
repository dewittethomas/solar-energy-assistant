import math
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from core.settings import get_settings
from models.model_features import WEATHER_COLUMNS
from models.prediction import Prediction
from repositories.prediction_repository import PredictionRepository
from responses.prediction_result import PredictionResult
from services.cache_service import CacheService
from services.geocoding_service import GeocodingService
from services.model_service import ModelService
from services.weather_service import WeatherService

class PredictionService:
    def __init__(
        self,
        weather_service: WeatherService,
        geocoding_service: GeocodingService,
        prediction_repository: PredictionRepository,
        model_service: ModelService,
        cache_service: CacheService | None = None
    ) -> None:
        self.weather_service = weather_service
        self.geocoding_service = geocoding_service
        self.repository = prediction_repository
        self.model_service = model_service
        self.cache_service = cache_service
        self.settings = get_settings()

    def predict_solar_yield(
        self,
        installation_id: str,
        start_date: str,
        end_date: str
    ) -> PredictionResult:
        self._validate_forecast_dates(start_date, end_date)
        model = self.model_service.get_active_model(
            installation_id=installation_id,
            target_column='solar_power_w'
        )

        if not model:
            raise LookupError(
                'No active hourly prediction model found for this installation'
            )

        coords = self._get_coordinates()
        cache_key = (
            f'prediction:'
            f'{installation_id}:'
            f"{model['id']}:"
            f"{round(coords['latitude'], 5)}:"
            f"{round(coords['longitude'], 5)}:"
            f'{start_date}:{end_date}'
        )

        if self.cache_service:
            cached = self.cache_service.get(cache_key)

            if cached:
                try:
                    return PredictionResult.model_validate_json(cached)
                except ValueError:
                    self.cache_service.delete(cache_key)

        weather_data = self.weather_service.get_weather_forecast(
            coords['latitude'],
            coords['longitude'],
            self.settings.timezone,
            start_date,
            end_date
        )

        inputs, time_data = self._build_inputs(weather_data)

        result = self.repository.predict_solar_yield(
            Path(str(model['model_path'])),
            inputs,
            time_data
        )

        if self.cache_service:
            self.cache_service.set(
                cache_key,
                result.model_dump_json(),
                expire=3600
            )

        return result

    def _validate_forecast_dates(
        self,
        start_date: str,
        end_date: str
    ) -> None:
        start = self._parse_date(start_date, 'start_date')
        end = self._parse_date(end_date, 'end_date')
        today = datetime.now(ZoneInfo(self.settings.timezone)).date()
        max_end_date = today + timedelta(days=14)

        if start < today:
            raise ValueError('start_date cannot be before today')

        if end < start:
            raise ValueError('end_date cannot be before start_date')

        if end > max_end_date:
            raise ValueError(
                f'end_date cannot be later than {max_end_date.isoformat()}'
            )

    def _parse_date(self, value: str, field_name: str) -> date:
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(
                f'{field_name} must use YYYY-MM-DD format'
            ) from exc

    def _get_coordinates(self) -> dict[str, float]:
        coords = self.geocoding_service.get_coordinates(self.settings.location)

        if not coords:
            raise ValueError(
                f'Invalid configured location: {self.settings.location}'
            )

        return coords

    def _build_inputs(
        self,
        weather_data: dict[str, object]
    ) -> tuple[list[Prediction], list[str]]:
        hourly = weather_data.get('hourly', {})
        if not isinstance(hourly, dict):
            raise ValueError('Weather response does not contain hourly data')

        times = hourly.get('time', [])

        if not isinstance(times, list):
            raise ValueError('Weather response time values must be a list')

        params = self._extract_weather_parameters(hourly)

        self._validate_data_consistency(times, params)

        if not times:
            raise ValueError('No hourly weather forecast data returned')

        inputs = []

        for index, time_value in enumerate(times):
            inputs.append(
                Prediction(
                    **{
                        column: params[column][index]
                        for column in WEATHER_COLUMNS
                    },
                    **self._calculate_time_features(str(time_value))
                )
            )

        return inputs, [str(time_value) for time_value in times]

    def _extract_weather_parameters(
        self,
        hourly: dict[str, object]
    ) -> dict[str, list[object]]:
        params = {}

        for column in WEATHER_COLUMNS:
            values = hourly.get(column, [])

            if not isinstance(values, list):
                raise ValueError(
                    f'Weather response values for {column} must be a list'
                )

            params[column] = values

        return params

    def _validate_data_consistency(
        self,
        times: list[object],
        params: dict[str, list[object]]
    ) -> None:
        expected_len = len(times)

        for key, values in params.items():
            if len(values) != expected_len:
                raise ValueError(
                    f'Mismatch in {key}: '
                    f'{len(values)} vs {expected_len}'
                )

    def _calculate_time_features(self, time_string: str) -> dict[str, float]:
        dt = datetime.fromisoformat(time_string)

        hour = dt.hour
        day_of_year = dt.timetuple().tm_yday

        return {
            'hour_sin': math.sin(2 * math.pi * hour / 24),
            'hour_cos': math.cos(2 * math.pi * hour / 24),
            'day_of_year_sin': math.sin(2 * math.pi * day_of_year / 365),
            'day_of_year_cos': math.cos(2 * math.pi * day_of_year / 365)
        }
