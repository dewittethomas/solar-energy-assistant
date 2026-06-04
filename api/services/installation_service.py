from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from core.settings import get_settings
from models.installation import InstallationCreate
from models.installation_configuration import InstallationConfigurationUpdate
from repositories.metadata_repository import MetadataRepository
from responses.dashboard_result import (
    DashboardResult,
    TomorrowWeatherResult,
    WeatherSummaryResult,
)
from responses.installation_configuration_result import (
    InstallationConfigurationResult,
)
from responses.prediction_result import PredictionResult
from services.consuming_activity_catalog import ConsumingActivityCatalog
from services.consuming_activity_seeder import ConsumingActivitySeeder
from services.geocoding_service import GeocodingService
from services.prediction_service import PredictionService
from services.weather_service import WeatherService


class InstallationService:
    def __init__(
        self,
        metadata_repository: MetadataRepository,
        prediction_service: PredictionService,
        weather_service: WeatherService,
        geocoding_service: GeocodingService,
        activity_catalog: ConsumingActivityCatalog | None = None,
        activity_seeder: ConsumingActivitySeeder | None = None,
    ) -> None:
        self.metadata_repository = metadata_repository
        self.prediction_service = prediction_service
        self.weather_service = weather_service
        self.geocoding_service = geocoding_service
        self.activity_catalog = activity_catalog or ConsumingActivityCatalog()
        self.activity_seeder = activity_seeder or ConsumingActivitySeeder(
            self.activity_catalog
        )
        self.settings = get_settings()

    def create_installation(
        self,
        installation: InstallationCreate
    ) -> InstallationConfigurationResult:
        owner = self.metadata_repository.get_owner()

        if not owner:
            raise LookupError('Owner not found')

        coordinates = self._resolve_installation_coordinates(
            installation.city,
            installation.country,
        )
        created = self.metadata_repository.create_installation(
            owner_id=str(owner['id']),
            name=installation.name,
            country=installation.country,
            city=installation.city,
            latitude=coordinates['latitude'],
            longitude=coordinates['longitude'],
            panel_count=installation.panel_count,
            capacity_kwp=installation.capacity_kwp,
        )
        self.metadata_repository.save_installation_configuration(
            str(created['installation_id']),
            InstallationConfigurationUpdate(
                name=installation.name,
                country=installation.country,
                city=installation.city,
                panel_count=installation.panel_count,
                capacity_kwp=installation.capacity_kwp,
                consuming_activities=self.activity_catalog.list_defaults(),
            )
        )

        return InstallationConfigurationResult.model_validate(
            self._with_available_activities(
                self.seed_default_consuming_activities(
                    str(created['installation_id']),
                    self.metadata_repository.get_installation_configuration(
                        str(created['installation_id'])
                    )
                )
            )
        )

    def get_configuration(
        self,
        installation_id: str
    ) -> InstallationConfigurationResult:
        configuration = self.metadata_repository.get_installation_configuration(
            installation_id
        )

        return InstallationConfigurationResult.model_validate(
            self._with_available_activities(
                self.seed_default_consuming_activities(
                    installation_id,
                    configuration,
                )
            )
        )

    def get_active_configuration(self) -> InstallationConfigurationResult:
        configuration = self.metadata_repository.get_active_installation_configuration()

        if not configuration:
            raise LookupError('Active installation not found')

        return InstallationConfigurationResult.model_validate(
            self._with_available_activities(
                self.seed_default_consuming_activities(
                    str(configuration['installation_id']),
                    configuration,
                )
            )
        )

    def save_configuration(
        self,
        installation_id: str,
        configuration: InstallationConfigurationUpdate
    ) -> InstallationConfigurationResult:
        current = self.metadata_repository.get_installation_configuration(
            installation_id
        )

        if (
            configuration.city is not None
            or configuration.country is not None
        ):
            city = configuration.city or str(current.get('city') or '')
            country = configuration.country or str(current.get('country') or '')
            coordinates = self._resolve_installation_coordinates(
                city,
                country,
            )
            self.metadata_repository.update_installation_coordinates(
                installation_id,
                coordinates['latitude'],
                coordinates['longitude'],
            )

        saved_configuration = (
            self.metadata_repository.save_installation_configuration(
                installation_id,
                configuration
            )
        )

        return InstallationConfigurationResult.model_validate(
            self._with_available_activities(
                self.seed_default_consuming_activities(
                    installation_id,
                    saved_configuration,
                )
            )
        )

    def seed_default_consuming_activities(
        self,
        installation_id: str,
        configuration: dict[str, object] | None = None,
    ) -> dict[str, object]:
        current_configuration = configuration or (
            self.metadata_repository.get_installation_configuration(
                installation_id
            )
        )
        seeded_activities, changed = self.activity_seeder.seed(
            current_configuration.get('consuming_activities')
            if current_configuration else None
        )

        if not changed:
            return current_configuration

        return self.metadata_repository.save_installation_configuration(
            installation_id,
            InstallationConfigurationUpdate(
                name=str(current_configuration.get('name') or '') or None,
                country=str(current_configuration.get('country') or '') or None,
                city=str(current_configuration.get('city') or '') or None,
                panel_count=current_configuration.get('panel_count'),
                capacity_kwp=current_configuration.get('capacity_kwp'),
                consuming_activities=seeded_activities,
            )
        )

    def list_available_consuming_activities(self) -> list[dict[str, object]]:
        return [
            activity.model_dump()
            for activity in self.activity_catalog.list_defaults()
        ]

    def predict(
        self,
        installation_id: str,
        start_date: str,
        end_date: str
    ) -> PredictionResult:
        return self.prediction_service.predict_solar_yield(
            installation_id=installation_id,
            start_date=start_date,
            end_date=end_date
        )

    def get_dashboard(self, installation_id: str) -> DashboardResult:
        now = datetime.now(ZoneInfo(self.settings.timezone))
        today = now.date()
        tomorrow = today + timedelta(days=1)
        predictions = self._get_predictions_or_none(
            installation_id,
            today.isoformat(),
            today.isoformat()
        )
        weather = self._get_weather_or_empty(
            installation_id,
            today.isoformat(),
            tomorrow.isoformat()
        )

        return DashboardResult(
            installation_id=installation_id,
            current_output_kw=self._current_output_kw(predictions, now),
            todays_yield_kwh=self._todays_yield_kwh(predictions),
            todays_peak_time_window=self._peak_time_window(predictions),
            current_weather=self._current_weather(weather, now),
            tomorrow_weather=self._tomorrow_weather(weather, tomorrow)
        )

    def _with_available_activities(
        self,
        configuration: dict[str, object]
    ) -> dict[str, object]:
        configuration['available_consuming_activities'] = (
            self.list_available_consuming_activities()
        )

        return configuration

    def _get_predictions_or_none(
        self,
        installation_id: str,
        start_date: str,
        end_date: str
    ) -> PredictionResult | None:
        try:
            return self.prediction_service.predict_solar_yield(
                installation_id=installation_id,
                start_date=start_date,
                end_date=end_date
            )
        except LookupError:
            return None

    def _get_weather_or_empty(
        self,
        installation_id: str,
        start_date: str,
        end_date: str
    ) -> dict[str, object]:
        coords = self._get_installation_coordinates(installation_id)

        if not coords:
            return {}

        try:
            return self.weather_service.get_weather_forecast(
                coords['latitude'],
                coords['longitude'],
                self.settings.timezone,
                start_date,
                end_date
            )
        except RuntimeError:
            return {}

    def _get_installation_coordinates(
        self,
        installation_id: str
    ) -> dict[str, float] | None:
        installation = self.metadata_repository.get_installation_configuration(
            installation_id
        )

        if not installation:
            return None

        latitude = installation.get('latitude')
        longitude = installation.get('longitude')

        if latitude is not None and longitude is not None:
            return {
                'latitude': float(latitude),
                'longitude': float(longitude),
            }

        city = installation.get('city')
        country = installation.get('country')

        if not isinstance(city, str) or not city.strip():
            return None

        if not isinstance(country, str) or not country.strip():
            return None

        coords = self.geocoding_service.get_coordinates(
            self._build_location_query(city, country)
        )

        if not coords:
            return None

        self.metadata_repository.update_installation_coordinates(
            installation_id,
            float(coords['latitude']),
            float(coords['longitude']),
        )
        return {
            'latitude': float(coords['latitude']),
            'longitude': float(coords['longitude']),
        }

    def _resolve_installation_coordinates(
        self,
        city: str,
        country: str
    ) -> dict[str, float]:
        reference = self.geocoding_service.get_coordinates(
            self._build_location_query(city, country)
        )

        if not reference:
            raise ValueError('Unable to geocode installation location')

        return {
            'latitude': float(reference['latitude']),
            'longitude': float(reference['longitude']),
        }

    def _build_location_query(self, city: str, country: str) -> str:
        return f'{city.strip()}, {country.strip()}'

    def _current_output_kw(
        self,
        predictions: PredictionResult | None,
        now: datetime
    ) -> float | None:
        if not predictions:
            return None

        for prediction in predictions.predictions:
            if (
                prediction.timestamp.date() == now.date()
                and prediction.timestamp.hour == now.hour
            ):
                return round(prediction.value / 1000, 3)

        return None

    def _todays_yield_kwh(
        self,
        predictions: PredictionResult | None
    ) -> float | None:
        if not predictions or not predictions.predictions:
            return None

        total_wh = sum(
            prediction.value
            for prediction in predictions.predictions
            if prediction.timestamp.date() == datetime.now(
                ZoneInfo(self.settings.timezone)
            ).date()
        )

        return round(total_wh / 1000, 3)

    def _peak_time_window(
        self,
        predictions: PredictionResult | None
    ) -> str | None:
        if not predictions or not predictions.predictions:
            return None

        todays_predictions = [
            prediction
            for prediction in predictions.predictions
            if prediction.timestamp.date() == datetime.now(
                ZoneInfo(self.settings.timezone)
            ).date()
        ]

        if not todays_predictions:
            return None

        peak = max(
            todays_predictions,
            key=lambda prediction: prediction.value
        )
        end_hour = (peak.timestamp.hour + 1) % 24

        return f'{peak.timestamp.strftime("%H:%M")}-{end_hour:02d}:00'

    def _current_weather(
        self,
        weather: dict[str, object],
        now: datetime
    ) -> WeatherSummaryResult:
        hourly = weather.get('hourly', {})

        if not isinstance(hourly, dict):
            return WeatherSummaryResult()

        index = self._find_hour_index(hourly, now)

        return WeatherSummaryResult(
            temperature_c=self._value_at(hourly, 'temperature_2m', index),
            status=self._weather_status(hourly, index)
        )

    def _tomorrow_weather(
        self,
        weather: dict[str, object],
        tomorrow
    ) -> TomorrowWeatherResult:
        hourly = weather.get('hourly', {})

        if not isinstance(hourly, dict):
            return TomorrowWeatherResult()

        indexes = self._indexes_for_day(hourly, tomorrow.isoformat())
        temperatures = [
            self._value_at(hourly, 'temperature_2m', index)
            for index in indexes
        ]
        temperatures = [
            value
            for value in temperatures
            if value is not None
        ]

        return TomorrowWeatherResult(
            min_temperature_c=round(min(temperatures), 1) if temperatures else None,
            max_temperature_c=round(max(temperatures), 1) if temperatures else None,
            status=self._weather_status(hourly, indexes[0]) if indexes else None
        )

    def _find_hour_index(
        self,
        hourly: dict[str, object],
        value: datetime
    ) -> int | None:
        times = hourly.get('time', [])

        if not isinstance(times, list):
            return None

        prefix = value.strftime('%Y-%m-%dT%H')

        for index, time_value in enumerate(times):
            if str(time_value).startswith(prefix):
                return index

        return None

    def _indexes_for_day(
        self,
        hourly: dict[str, object],
        day: str
    ) -> list[int]:
        times = hourly.get('time', [])

        if not isinstance(times, list):
            return []

        return [
            index
            for index, time_value in enumerate(times)
            if str(time_value).startswith(day)
        ]

    def _value_at(
        self,
        hourly: dict[str, object],
        key: str,
        index: int | None
    ) -> float | None:
        values = hourly.get(key, [])

        if index is None or not isinstance(values, list) or index >= len(values):
            return None

        return float(values[index])

    def _weather_status(
        self,
        hourly: dict[str, object],
        index: int | None
    ) -> str | None:
        cloud_cover = self._value_at(hourly, 'cloud_cover', index)

        if cloud_cover is None:
            return None

        if cloud_cover < 25:
            return 'sunny'

        if cloud_cover < 70:
            return 'partly_cloudy'

        return 'cloudy'
