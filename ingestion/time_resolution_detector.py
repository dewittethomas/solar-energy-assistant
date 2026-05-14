import pandas as pd

from models.time_resolution import TimeResolution


class TimeResolutionDetector:
    def detect(self, df: pd.DataFrame) -> TimeResolution:
        if 'timestamp' not in df.columns:
            raise ValueError('Missing timestamp column')

        timestamps = (
            pd.to_datetime(df['timestamp'], errors='coerce')
            .dropna()
            .drop_duplicates()
            .sort_values()
        )

        if len(timestamps) < 2:
            return TimeResolution('unknown', None)

        if self._looks_monthly(timestamps):
            return TimeResolution('monthly', None)

        intervals = timestamps.diff().dropna()
        median_interval = intervals.median()
        interval_minutes = median_interval.total_seconds() / 60

        if interval_minutes <= 60:
            return TimeResolution('hourly', interval_minutes)

        return TimeResolution('unknown', interval_minutes)

    def _looks_monthly(self, timestamps: pd.Series) -> bool:
        month_numbers = timestamps.dt.to_period('M').map(
            lambda period: period.ordinal
        )
        month_steps = month_numbers.diff().dropna()

        if month_steps.empty:
            return False

        monthly_step_ratio = (month_steps == 1).mean()
        same_month_count = timestamps.dt.to_period('M').nunique()

        return (
            monthly_step_ratio >= 0.8
            and same_month_count == len(timestamps)
        )
