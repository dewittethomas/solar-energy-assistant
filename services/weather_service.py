from repositories.weather_repository import WeatherRepository

class WeatherService:
    def __init__(
        self,
        repository: WeatherRepository | None = None
    ) -> None:
        self.repository = repository or WeatherRepository()

    def get_weather_forecast(
        self,
        latitude: float,
        longitude: float,
        timezone: str,
        start_date: str,
        end_date: str
    ) -> dict[str, object]:
        return self.repository.fetch_forecast_data(
            latitude,
            longitude,
            timezone,
            start_date,
            end_date
        )

    def get_historical_weather(
        self,
        latitude: float,
        longitude: float,
        timezone: str,
        start_date: str,
        end_date: str
    ) -> dict[str, object]:
        return self.repository.fetch_historical_data(
            latitude,
            longitude,
            timezone,
            start_date,
            end_date
        )
