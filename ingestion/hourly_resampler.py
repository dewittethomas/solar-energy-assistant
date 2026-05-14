import pandas as pd

from ingestion.time_resolution_detector import TimeResolutionDetector

class HourlyResampler:
    def resample(self, df: pd.DataFrame) -> pd.DataFrame:
        resolution = TimeResolutionDetector().detect(df)

        if resolution.kind == 'monthly':
            return df.copy()

        value_column = self._get_value_column(df)
        aggregation = (
            'mean'
            if value_column == 'power_kw'
            else lambda values: values.sum(min_count=1)
        )

        source = df.copy()
        source['timestamp'] = pd.to_datetime(
            source['timestamp'],
            errors='coerce'
        )
        source = source.dropna(subset=['timestamp', value_column])

        grouped = (
            source
            .set_index('timestamp')
            .groupby('installation_id')
            .resample('h')[value_column]
            .agg(aggregation)
            .dropna()
            .reset_index()
        )

        return grouped[
            ['installation_id', 'timestamp', value_column]
        ].reset_index(drop=True)

    def _get_value_column(self, df: pd.DataFrame) -> str:
        value_columns = [
            column
            for column in ('power_kw', 'energy_kwh')
            if column in df.columns
        ]

        if len(value_columns) != 1:
            raise ValueError(
                'Expected exactly one value column: power_kw or energy_kwh'
            )

        return value_columns[0]
