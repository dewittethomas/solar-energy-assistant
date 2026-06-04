from pydantic import BaseModel


class WeatherSummaryResult(BaseModel):
    temperature_c: float | None = None
    status: str | None = None


class TomorrowWeatherResult(BaseModel):
    min_temperature_c: float | None = None
    max_temperature_c: float | None = None
    status: str | None = None


class DashboardResult(BaseModel):
    installation_id: str
    current_output_kw: float | None
    todays_yield_kwh: float | None
    todays_peak_time_window: str | None
    current_weather: WeatherSummaryResult
    tomorrow_weather: TomorrowWeatherResult

