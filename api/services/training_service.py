import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import pandas as pd

from core.settings import get_settings
from models.model_features import (
    FEATURE_COLUMNS,
    add_cyclical_time_features,
    generate_solar_position_data,
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

    def queue_training_run(self, parquet_path: Path) -> dict[str, object]:
        dataset_info = self.metadata_service.inspect_parquet_dataset(parquet_path)
        existing_run = self.metadata_service.get_latest_incomplete_training_run(
            str(dataset_info['installation_id'])
        )

        if existing_run:
            raise ValueError(
                'A training run is already in progress for this installation'
            )

        return self.metadata_service.create_training_run(
            installation_id=str(dataset_info['installation_id']),
            status='queued',
            phase='queued',
            progress=0,
        )

    def train_from_parquet(
        self,
        training_run_id: str,
        parquet_path: Path,
        optimize: bool = False,
        n_trials: int = 50,
        activate_model: bool = False
    ) -> ModelTrainingResult:
        try:
            self._update_run(
                training_run_id,
                status='running',
                phase='validating_dataset',
                progress=10,
                error_code='none',
            )
            source = self._read_training_source(parquet_path)
            dataset = self.metadata_service.register_parquet_dataset(parquet_path)
            self._update_run(
                training_run_id,
                dataset_id=str(dataset['id']),
                phase='preparing_features',
                progress=25,
                error_code='none',
            )
            weather_data = self._fetch_historical_weather(
                str(dataset['installation_id']),
                source.data,
            )
            training_data = self._build_training_data(source, weather_data)
            output_path = self._build_output_path(parquet_path)
            self._update_run(
                training_run_id,
                phase='optimizing' if optimize else 'training_final_model',
                progress=35 if optimize else 80,
                total_trials=n_trials if optimize else None,
                current_trial=0 if optimize else None,
                best_rmse=None,
                error_code='none',
            )
            result = self.training_repository.train_and_export(
                features=training_data[source.feature_columns],
                target=training_data[source.target_column],
                output_path=output_path,
                optimize=optimize,
                n_trials=n_trials,
                trial_callback=(
                    lambda current_trial, total_trials, best_rmse:
                    self._update_run(
                        training_run_id,
                        phase='optimizing',
                        progress=35 + int((current_trial / total_trials) * 40),
                        current_trial=current_trial,
                        total_trials=total_trials,
                        best_rmse=best_rmse,
                        error_code='none',
                    )
                ) if optimize else None,
            )
            model_path = self._format_path(result['model_path'])
            self._update_run(
                training_run_id,
                phase='training_final_model',
                progress=80,
                error_code='none',
            )
            model_quality = self.evaluation_service.build_model_quality(
                diagnosis=result['overfitting'],
                metrics=result['metrics']
            )
            self._update_run(
                training_run_id,
                phase='evaluating',
                progress=90,
                error_code='none',
            )
            should_activate = True
            self._update_run(
                training_run_id,
                phase='saving_model',
                progress=95,
                error_code='none',
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
            summary = self._build_summary(source.data, training_data)
            self.metadata_service.finish_training_run(
                run_id=training_run_id,
                status='completed',
                model_id=str(model['id']),
            )
            self._update_run(
                training_run_id,
                phase='completed',
                progress=100,
                best_rmse=result['metrics']['rmse'],
                summary=summary,
                error_code='none',
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
            current_run = self.metadata_service.get_training_run(training_run_id)
            self._update_run(
                training_run_id,
                status='failed',
                phase='failed',
                progress=int(current_run['progress']) if current_run else 0,
                error_code=self._error_code_for(exc),
            )
            raise

    def _read_training_source(self, parquet_path: Path) -> TrainingSource:
        if not parquet_path.exists():
            raise ValueError(f'Parquet file does not exist: {parquet_path}')

        df = pd.read_parquet(parquet_path)

        if 'timestamp' not in df.columns:
            raise ValueError('Training parquet must contain timestamp')

        if 'power_kw' not in df.columns:
            raise ValueError('Training parquet must contain power_kw')

        return TrainingSource(
            data=self._read_solar_power_data(df),
            feature_columns=FEATURE_COLUMNS,
            target_column='solar_power_w'
        )

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

    def _fetch_historical_weather(
        self,
        installation_id: str,
        solar_data: pd.DataFrame
    ) -> pd.DataFrame:
        coords = self._get_installation_coordinates(installation_id)

        if not coords:
            raise ValueError(
                f'Invalid configured location for installation {installation_id}'
            )

        start_date = solar_data['timestamp'].min()
        end_date = solar_data['timestamp'].max()

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
        solar_position_data = generate_solar_position_data(
            start_date=start_date.date().isoformat(),
            end_date=(end_date.normalize() + pd.Timedelta(days=1)),
            latitude=coords['latitude'],
            longitude=coords['longitude'],
            timezone=self.settings.timezone,
            frequency='h',
        ).rename(columns={'datetime': 'timestamp'})

        return weather_data.drop(columns=['time']).merge(
            solar_position_data,
            on='timestamp',
            how='left',
        )

    def _get_installation_coordinates(
        self,
        installation_id: str
    ) -> dict[str, float] | None:
        configuration = self.metadata_service.repository.get_installation_configuration(
            installation_id
        )

        if not configuration:
            return None

        latitude = configuration.get('latitude')
        longitude = configuration.get('longitude')

        if latitude is not None and longitude is not None:
            return {
                'latitude': float(latitude),
                'longitude': float(longitude),
            }

        city = configuration.get('city')
        country = configuration.get('country')

        if (
            isinstance(city, str)
            and city.strip()
            and isinstance(country, str)
            and country.strip()
        ):
            coords = self.geocoding_service.get_coordinates(
                f'{city.strip()}, {country.strip()}'
            )

            if coords:
                self.metadata_service.repository.update_installation_coordinates(
                    installation_id,
                    float(coords['latitude']),
                    float(coords['longitude']),
                )
                return {
                    'latitude': float(coords['latitude']),
                    'longitude': float(coords['longitude']),
                }

        return None

    def _build_training_data(
        self,
        source: TrainingSource,
        weather_data: pd.DataFrame
    ) -> pd.DataFrame:
        return self._build_hourly_training_data(source.data, weather_data)

    def _build_hourly_training_data(
        self,
        solar_data: pd.DataFrame,
        weather_data: pd.DataFrame
    ) -> pd.DataFrame:
        df = solar_data.merge(weather_data, on='timestamp', how='inner')

        if df.empty:
            raise ValueError('No matching solar and weather timestamps found')

        df = add_cyclical_time_features(df)

        return df.dropna(subset=[*FEATURE_COLUMNS, 'solar_power_w'])

    def _build_output_path(
        self,
        parquet_path: Path
    ) -> Path:
        safe_name = self._safe_name(parquet_path.stem)

        return (
            self.settings.model_storage_dir
            / f'{safe_name}-trained-{uuid4().hex}.onnx'
        )

    def _safe_name(self, value: str) -> str:
        safe_value = re.sub(r'[^A-Za-z0-9_.-]+', '-', value).strip('.-')

        return safe_value or 'model'

    def _format_path(self, path: Path) -> str:
        try:
            return path.relative_to(Path.cwd()).as_posix()
        except ValueError:
            return path.as_posix()

    def _update_run(
        self,
        training_run_id: str,
        **changes: object
    ) -> None:
        normalized_changes = {
            key: value
            for key, value in changes.items()
            if value is not None
        }

        if normalized_changes.get('error_code') == 'none':
            normalized_changes['error_code'] = None

        self.metadata_service.update_training_run(
            training_run_id,
            **normalized_changes,
        )

    def _error_code_for(self, exc: Exception) -> str:
        message = str(exc).lower()

        if 'missing' in message and 'column' in message:
            return 'missing_required_column'

        if 'at least 10 matched training rows' in message:
            return 'not_enough_rows'

        if 'parquet file does not exist' in message:
            return 'invalid_csv_format'

        if 'save_model' in message or 'onnx' in message:
            return 'model_save_failed'

        return 'training_failed'

    def _build_summary(
        self,
        source_data: pd.DataFrame,
        training_data: pd.DataFrame
    ) -> dict[str, object]:
        timestamps = pd.to_datetime(source_data['timestamp'], errors='coerce').dropna()
        daily_energy = (
            source_data.assign(
                date=pd.to_datetime(source_data['timestamp'], errors='coerce').dt.date,
                energy_kwh=pd.to_numeric(
                    source_data['solar_power_w'],
                    errors='coerce'
                ) / 1000,
            )
            .dropna(subset=['date', 'energy_kwh'])
            .groupby('date', as_index=False)['energy_kwh']
            .sum()
        )
        hourly_profile = (
            source_data.assign(
                hour=pd.to_datetime(source_data['timestamp'], errors='coerce').dt.hour,
                power_kw=pd.to_numeric(
                    source_data['solar_power_w'],
                    errors='coerce'
                ) / 1000,
            )
            .dropna(subset=['hour', 'power_kw'])
            .groupby('hour', as_index=False)['power_kw']
            .mean()
        )
        best_window_start, best_window_end = self._best_window(hourly_profile)

        return {
            'records': len(training_data),
            'period_start': timestamps.min().date().isoformat(),
            'period_end': timestamps.max().date().isoformat(),
            'best_window_start': best_window_start,
            'best_window_end': best_window_end,
            'average_daily_production_kwh': round(
                float(daily_energy['energy_kwh'].mean()) if not daily_energy.empty else 0.0,
                3,
            ),
        }

    def _best_window(self, hourly_profile: pd.DataFrame) -> tuple[str, str]:
        if hourly_profile.empty:
            return '00:00', '00:00'

        best_start = 0
        best_sum = float('-inf')
        values = {int(row['hour']): float(row['power_kw']) for _, row in hourly_profile.iterrows()}

        for start_hour in range(0, 21):
            window_sum = sum(values.get(hour, 0.0) for hour in range(start_hour, start_hour + 4))
            if window_sum > best_sum:
                best_sum = window_sum
                best_start = start_hour

        return f'{best_start:02d}:00', f'{best_start + 4:02d}:00'
