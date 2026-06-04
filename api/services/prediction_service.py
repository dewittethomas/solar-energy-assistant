from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from core.settings import get_settings
import pandas as pd

from models.model_features import (
    FEATURE_COLUMNS,
    WEATHER_COLUMNS,
    add_cyclical_time_features,
    generate_solar_position_data,
)
from models.prediction import Prediction
from repositories.prediction_repository import PredictionRepository
from responses.prediction_result import PredictionResult
from services.cache_service import CacheService
from services.geocoding_service import GeocodingService
from services.metadata_service import MetadataService
from services.model_service import ModelService
from services.weather_service import WeatherService

class ModelNotReadyError(Exception):
    def __init__(self, training_run_id: str) -> None:
        self.training_run_id = training_run_id
        super().__init__('model_training_in_progress')

class PredictionService:
    def __init__(
        self,
        weather_service: WeatherService,
        geocoding_service: GeocodingService,
        prediction_repository: PredictionRepository,
        model_service: ModelService,
        metadata_service: MetadataService,
        cache_service: CacheService | None = None
    ) -> None:
        self.weather_service = weather_service
        self.geocoding_service = geocoding_service
        self.repository = prediction_repository
        self.model_service = model_service
        self.metadata_service = metadata_service
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
            training_run = self.metadata_service.get_latest_incomplete_training_run(
                installation_id
            )

            if training_run:
                raise ModelNotReadyError(str(training_run['id']))

            raise LookupError(
                'No active hourly prediction model found for this installation'
            )

        coords = self._get_coordinates(installation_id)
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

        inputs, time_data = self._build_inputs(weather_data, coords)

        result = self.repository.predict_solar_yield(
            Path(str(model['model_path'])),
            inputs,
            time_data
        )
        result = self._apply_capacity_guard(
            installation_id=installation_id,
            predictions=result,
        )

        if self.cache_service:
            self.cache_service.set(
                cache_key,
                result.model_dump_json(),
                expire=3600
            )

        return result

    def _apply_capacity_guard(
        self,
        installation_id: str,
        predictions: PredictionResult,
    ) -> PredictionResult:
        installation = self.metadata_service.repository.get_installation_configuration(
            installation_id
        )
        capacity_kwp = installation.get('capacity_kwp') if installation else None

        if capacity_kwp in (None, ''):
            return predictions

        capacity_w = float(capacity_kwp) * 1000
        max_prediction_w = capacity_w * 1.2
        clamped_points = [
            point.model_copy(update={'value': min(float(point.value), max_prediction_w)})
            for point in predictions.predictions
        ]
        total_average = (
            sum(point.value for point in clamped_points) / len(clamped_points)
            if clamped_points
            else 0.0
        )

        return predictions.model_copy(
            update={
                'total_average': float(total_average),
                'predictions': clamped_points,
            }
        )

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

    def _get_coordinates(self, installation_id: str) -> dict[str, float]:
        installation = self.metadata_service.repository.get_installation_configuration(
            installation_id
        )

        latitude = installation.get('latitude') if installation else None
        longitude = installation.get('longitude') if installation else None

        if latitude is not None and longitude is not None:
            return {
                'latitude': float(latitude),
                'longitude': float(longitude),
            }

        location = self._get_installation_location(installation_id)
        coords = self.geocoding_service.get_coordinates(location)

        if not coords:
            raise ValueError(
                f'Invalid configured location: {location}'
            )

        self.metadata_service.repository.update_installation_coordinates(
            installation_id,
            float(coords['latitude']),
            float(coords['longitude']),
        )
        return coords

    def _get_installation_location(self, installation_id: str) -> str:
        configuration = self.metadata_service.repository.get_installation_configuration(
            installation_id
        )
        city = configuration.get('city') if configuration else None
        country = configuration.get('country') if configuration else None

        if (
            isinstance(city, str)
            and city.strip()
            and isinstance(country, str)
            and country.strip()
        ):
            return f'{city.strip()}, {country.strip()}'

        return self.settings.location

    def _build_inputs(
        self,
        weather_data: dict[str, object],
        coords: dict[str, float],
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

        feature_frame = pd.DataFrame({
            'timestamp': pd.to_datetime(times, errors='coerce'),
            **{
                column: params[column]
                for column in WEATHER_COLUMNS
            },
        })
        solar_position_data = generate_solar_position_data(
            start_date=feature_frame['timestamp'].iloc[0],
            end_date=feature_frame['timestamp'].iloc[-1] + pd.Timedelta(hours=1),
            latitude=coords['latitude'],
            longitude=coords['longitude'],
            timezone=self.settings.timezone,
            frequency='h',
        ).rename(columns={'datetime': 'timestamp'})
        feature_frame = feature_frame.merge(
            solar_position_data,
            on='timestamp',
            how='left',
        )
        feature_frame = add_cyclical_time_features(feature_frame)
        feature_frame = feature_frame.dropna(subset=FEATURE_COLUMNS)

        inputs = []

        for _, row in feature_frame.iterrows():
            inputs.append(
                Prediction(
                    **{
                        column: float(row[column])
                        for column in FEATURE_COLUMNS
                    }
                )
            )

        time_data = [
            pd.Timestamp(row['timestamp']).isoformat()
            for _, row in feature_frame.iterrows()
        ]

        return inputs, time_data

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
