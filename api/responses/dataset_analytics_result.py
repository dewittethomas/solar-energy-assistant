from pydantic import BaseModel


class AnalyticsPointResult(BaseModel):
    label: str
    value: float


class DatasetAnalyticsResult(BaseModel):
    dataset_id: str
    period_start: str
    period_end: str
    production_unit: str | None = None
    monthly_series: list[AnalyticsPointResult]
    seasonal_series: list[AnalyticsPointResult]
    best_month: str
    strongest_season: str
    best_window_start: str
    best_window_end: str
    peak_hour: str
    summer_winter_difference_pct: float
