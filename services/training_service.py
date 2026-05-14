import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

from core.settings import get_settings
from models.model_features import (
    FEATURE_COLUMNS,
    MONTHLY_FEATURE_COLUMNS,
    RADIATION_COLUMNS,
    WEATHER_COLUMNS,
)
from repositories.model_training_repository import ModelTrainingRepository
from responses.model_training_result import (
    ModelTrainingMetrics,
    ModelTrainingResult,
)
from services.evaluation_service import EvaluationService
from services.geocoding_service import GeocodingService
from services.metadata_service import MetadataService
from services.weather_service import WeatherService

@dataclass(frozen=True)
class TrainingSource:
    data: pd.DataFrame
    frequency: str
    feature_columns: list[str]
    target_column: str

class TrainingService:
    def __init__(
        self,
        weather_service: WeatherService,
        geocoding_service: GeocodingService,
        training_repository: ModelTrainingRepository,
        metadata_service: MetadataService | None = None,
        evaluation_service: EvaluationService | None = None
    ) -> None:
        self.weather_service = weather_service
        self.geocoding_service = geocoding_service
        self.training_repository = training_repository
        self.metadata_service = metadata_service or MetadataService()
        self.evaluation_service = evaluation_service or EvaluationService()
        self.settings = get_settings()

    def train_from_parquet(
        self,
        parquet_path: Path,
        optimize: bool = False,
        n_trials: int = 50,
        activate_model: bool = False
    ) -> ModelTrainingResult:
        source = self._read_training_source(parquet_path)
        dataset = self.metadata_service.register_parquet_dataset(parquet_path)
        training_run = self.metadata_service.start_training_run(
            dataset_id=str(dataset['id']),
            notes=f'{source.frequency} {source.target_column} training started'
        )

        try:
            weather_data = self._fetch_historical_weather(
                source.data,
                source.frequency
            )
            training_data = self._build_training_data(source, weather_data)
            output_path = self._build_output_path(parquet_path)
            result = self.training_repository.train_and_export(
                features=training_data[source.feature_columns],
                target=training_data[source.target_column],
                output_path=output_path,
                optimize=optimize,
                n_trials=n_trials,
                optimization_profile=source.frequency
            )
            model_path = self._format_path(result['model_path'])
            model_quality = self.evaluation_service.build_model_quality(
                diagnosis=result['overfitting'],
                metrics=result['metrics']
            )
            should_activate = (
                activate_model
                and self.evaluation_service.can_activate(model_quality)
            )
            model = self.metadata_service.register_model(
                dataset_id=str(dataset['id']),
                version=str(result['training_mode']),
                model_path=model_path,
                is_active=should_activate,
                metrics=result['metrics'],
                train_size=int(result['train_rows']),
                validation_size=int(result['validation_rows']),
                test_size=int(result['test_rows']),
                target_column=source.target_column
            )
            self.metadata_service.finish_training_run(
                run_id=str(training_run['id']),
                status='completed',
                model_id=str(model['id']),
                notes=self._build_training_run_notes(
                    activate_model,
                    should_activate,
                    model_quality.message
                )
            )

            return ModelTrainingResult(
                dataset_id=str(dataset['id']),
                model_id=str(model['id']),
                model_path=model_path,
                is_active=should_activate,
                source_path=self._format_path(parquet_path),
                training_rows=len(training_data),
                train_rows=result['train_rows'],
                validation_rows=result['validation_rows'],
                test_rows=result['test_rows'],
                feature_columns=source.feature_columns,
                target_column=source.target_column,
                optimized=optimize,
                training_mode=result['training_mode'],
                best_params=result['best_params'],
                metrics=ModelTrainingMetrics(**result['metrics']),
                model_quality=model_quality
            )
        except Exception as exc:
            self.metadata_service.finish_training_run(
                run_id=str(training_run['id']),
                status='failed',
                notes=str(exc)
            )
            raise

    def _read_training_source(self, parquet_path: Path) -> TrainingSource:
        if not parquet_path.exists():
            raise ValueError(f'Parquet file does not exist: {parquet_path}')

        df = pd.read_parquet(parquet_path)

        if 'timestamp' not in df.columns:
            raise ValueError('Training parquet must contain timestamp')

        if 'power_kw' in df.columns:
            return TrainingSource(
                data=self._read_solar_power_data(df),
                frequency='hourly',
                feature_columns=FEATURE_COLUMNS,
                target_column='solar_power_w'
            )

        if 'energy_kwh' in df.columns:
            return TrainingSource(
                data=self._read_solar_energy_data(df),
                frequency='monthly',
                feature_columns=MONTHLY_FEATURE_COLUMNS,
                target_column='solar_energy_kwh'
            )

        raise ValueError('Training parquet must contain power_kw or energy_kwh')

    def _read_solar_power_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df[['timestamp', 'power_kw']].copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['solar_power_w'] = pd.to_numeric(
            df['power_kw'],
            errors='coerce'
        ) * 1000
        df = df.dropna(subset=['timestamp', 'solar_power_w'])

        return (
            df
            .groupby('timestamp', as_index=False)['solar_power_w']
            .mean()
            .sort_values('timestamp')
            .reset_index(drop=True)
        )

    def _read_solar_energy_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df[['timestamp', 'energy_kwh']].copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['timestamp'] = df['timestamp'].dt.to_period('M').dt.to_timestamp()
        df['solar_energy_kwh'] = pd.to_numeric(
            df['energy_kwh'],
            errors='coerce'
        )
        df = df.dropna(subset=['timestamp', 'solar_energy_kwh'])
        df = self._drop_incomplete_months(df)

        if df.empty:
            raise ValueError(
                'Monthly energy training requires at least one completed month'
            )

        return (
            df
            .groupby('timestamp', as_index=False)['solar_energy_kwh']
            .sum()
            .sort_values('timestamp')
            .reset_index(drop=True)
        )

    def _drop_incomplete_months(self, df: pd.DataFrame) -> pd.DataFrame:
        today = (
            pd.Timestamp.now(tz=self.settings.timezone)
            .tz_localize(None)
            .normalize()
        )
        month_end = df['timestamp'] + pd.offsets.MonthEnd(0)

        return df.loc[month_end < today].copy()

    def _fetch_historical_weather(
        self,
        solar_data: pd.DataFrame,
        frequency: str
    ) -> pd.DataFrame:
        coords = self.geocoding_service.get_coordinates(self.settings.location)

        if not coords:
            raise ValueError(
                f'Invalid configured location: {self.settings.location}'
            )

        start_date = solar_data['timestamp'].min()
        end_date = solar_data['timestamp'].max()

        if frequency == 'monthly':
            start_date = start_date.to_period('M').to_timestamp()
            end_date = end_date.to_period('M').to_timestamp() + pd.offsets.MonthEnd(0)

        weather = self.weather_service.get_historical_weather(
            coords['latitude'],
            coords['longitude'],
            self.settings.timezone,
            start_date.date().isoformat(),
            end_date.date().isoformat()
        )
        hourly = weather.get('hourly', {})
        weather_data = pd.DataFrame(hourly)

        if weather_data.empty:
            raise ValueError('No historical weather data returned')

        weather_data['timestamp'] = pd.to_datetime(
            weather_data['time'],
            errors='coerce'
        )

        return weather_data.drop(columns=['time'])

    def _build_training_data(
        self,
        source: TrainingSource,
        weather_data: pd.DataFrame
    ) -> pd.DataFrame:
        if source.frequency == 'monthly':
            return self._build_monthly_training_data(source.data, weather_data)

        return self._build_hourly_training_data(source.data, weather_data)

    def _build_hourly_training_data(
        self,
        solar_data: pd.DataFrame,
        weather_data: pd.DataFrame
    ) -> pd.DataFrame:
        df = solar_data.merge(weather_data, on='timestamp', how='inner')

        if df.empty:
            raise ValueError('No matching solar and weather timestamps found')

        df['hour'] = df['timestamp'].dt.hour
        df['day_of_year'] = df['timestamp'].dt.dayofyear
        self._add_cyclical_features(df, 'hour', 24, 'hour_sin', 'hour_cos')
        self._add_cyclical_features(
            df,
            'day_of_year',
            365,
            'day_of_year_sin',
            'day_of_year_cos'
        )

        return df.dropna(subset=[*FEATURE_COLUMNS, 'solar_power_w'])

    def _build_monthly_training_data(
        self,
        solar_data: pd.DataFrame,
        weather_data: pd.DataFrame
    ) -> pd.DataFrame:
        monthly_weather = self._aggregate_monthly_weather(weather_data)
        df = solar_data.merge(monthly_weather, on='timestamp', how='inner')

        if df.empty:
            raise ValueError('No matching solar and weather months found')

        month_middle = (
            df['timestamp']
            + pd.to_timedelta(df['timestamp'].dt.days_in_month // 2, unit='D')
        )
        df['month'] = df['timestamp'].dt.month
        df['day_of_year'] = month_middle.dt.dayofyear
        self._add_cyclical_features(df, 'month', 12, 'month_sin', 'month_cos')
        self._add_cyclical_features(
            df,
            'day_of_year',
            365,
            'day_of_year_sin',
            'day_of_year_cos'
        )

        return df.dropna(subset=[*MONTHLY_FEATURE_COLUMNS, 'solar_energy_kwh'])

    def _add_cyclical_features(
        self,
        df: pd.DataFrame,
        source_column: str,
        period: int,
        sine_column: str,
        cosine_column: str
    ) -> None:
        angle = 2 * np.pi * df[source_column] / period
        df[sine_column] = np.sin(angle)
        df[cosine_column] = np.cos(angle)

    def _aggregate_monthly_weather(
        self,
        weather_data: pd.DataFrame
    ) -> pd.DataFrame:
        weather = weather_data.copy()
        weather['timestamp'] = pd.to_datetime(weather['timestamp'], errors='coerce')
        weather = weather.dropna(subset=['timestamp'])

        for column in WEATHER_COLUMNS:
            weather[column] = pd.to_numeric(weather[column], errors='coerce')

        weather['timestamp'] = weather['timestamp'].dt.to_period('M').dt.to_timestamp()
        aggregation = {
            'cloud_cover': 'mean',
            **{
                column: 'sum'
                for column in RADIATION_COLUMNS
            }
        }

        return (
            weather
            .groupby('timestamp', as_index=False)
            .agg(aggregation)
        )

    def _build_output_path(
        self,
        parquet_path: Path
    ) -> Path:
        safe_name = self._safe_name(parquet_path.stem)

        return (
            self.settings.model_storage_dir
            / f'{safe_name}-trained-{uuid4().hex}.onnx'
        )

    def _build_training_run_notes(
        self,
        activate_model: bool,
        should_activate: bool,
        quality_message: str
    ) -> str:
        if should_activate:
            return 'Training completed and model was activated'

        if activate_model:
            return f'Training completed but model was not activated. {quality_message}'

        return 'Training completed'

    def _safe_name(self, value: str) -> str:
        safe_value = re.sub(r'[^A-Za-z0-9_.-]+', '-', value).strip('.-')

        return safe_value or 'model'

    def _format_path(self, path: Path) -> str:
        try:
            return path.relative_to(Path.cwd()).as_posix()
        except ValueError:
            return path.as_posix()
