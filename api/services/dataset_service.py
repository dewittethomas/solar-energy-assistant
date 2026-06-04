from pathlib import Path
import json
import re

import pandas as pd
from repositories.dataset_repository import DatasetRepository

class DatasetService:
    def __init__(
        self,
        repository: DatasetRepository | None = None
    ) -> None:
        self.repository = repository or DatasetRepository()

    def list_datasets(
        self,
        limit: int = 100,
        offset: int = 0,
        installation_id: str | None = None
    ) -> list[dict[str, object]]:
        datasets = self.repository.list_datasets(limit, offset, installation_id)
        return [self._enrich_dataset(dataset) for dataset in datasets]

    def get_dataset(self, dataset_id: str) -> dict[str, object] | None:
        dataset = self.repository.get(dataset_id)
        return self._enrich_dataset(dataset) if dataset else None

    def get_dataset_analytics(self, dataset_id: str) -> dict[str, object] | None:
        dataset = self.get_dataset(dataset_id)

        if not dataset:
            return None

        dataset_path = Path(str(dataset['path']))

        if not dataset_path.is_absolute():
            dataset_path = Path.cwd() / dataset_path

        df = pd.read_parquet(dataset_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['power_kw'] = pd.to_numeric(df['power_kw'], errors='coerce').fillna(0)
        df = df.dropna(subset=['timestamp']).sort_values('timestamp')

        if df.empty:
            raise ValueError('Dataset does not contain any usable rows')

        df['month'] = df['timestamp'].dt.month
        df['hour'] = df['timestamp'].dt.hour
        df['timestamp_year'] = df['timestamp'].dt.year
        df['season'] = df['month'].map(_month_to_season)
        df['season_year'] = df['timestamp'].dt.year + (
            df['month'] == 12
        ).astype(int)
        df['interval_hours'] = _infer_interval_hours(df['timestamp'])
        df['energy_kwh'] = df['power_kw'] * df['interval_hours']

        monthly_totals = (
            df.groupby(['timestamp_year', 'month'], as_index=False)['energy_kwh']
            .sum()
        )
        monthly = (
            monthly_totals.groupby('month', as_index=False)['energy_kwh']
            .mean()
            .sort_values('month')
        )
        seasonal_totals = (
            df.groupby(['season_year', 'season'], as_index=False)['energy_kwh']
            .sum()
        )
        seasonal = (
            seasonal_totals.groupby('season', as_index=False)['energy_kwh']
            .mean()
        )
        hourly = (
            df.groupby('hour', as_index=False)['power_kw']
            .mean()
            .sort_values('hour')
        )

        hourly_values = hourly['power_kw'].tolist()
        window_hours = hourly['hour'].tolist()
        best_window = _best_three_hour_window(window_hours, hourly_values)
        strongest_season = max(
            seasonal.to_dict('records'),
            key=lambda row: row['energy_kwh']
        )
        summer_average = (
            float(seasonal[seasonal['season'] == 'summer']['energy_kwh'].iloc[0])
            if any(seasonal['season'] == 'summer') else 0.0
        )
        winter_average = (
            float(seasonal[seasonal['season'] == 'winter']['energy_kwh'].iloc[0])
            if any(seasonal['season'] == 'winter') else 0.0
        )
        comparison = ((summer_average - winter_average) / winter_average * 100) if winter_average else 0.0

        return {
            'dataset_id': str(dataset['id']),
            'period_start': df['timestamp'].min().isoformat(),
            'period_end': df['timestamp'].max().isoformat(),
            'production_unit': _history_unit_from_dataset(
                str(dataset.get('production_unit') or 'kW')
            ),
            'monthly_series': [
                {'label': _month_label(int(row['month'])), 'value': float(row['energy_kwh'])}
                for row in monthly.to_dict('records')
            ],
            'seasonal_series': [
                {'label': str(row['season']), 'value': float(row['energy_kwh'])}
                for row in seasonal.to_dict('records')
            ],
            'best_month': _month_label(int(monthly.loc[monthly['energy_kwh'].idxmax(), 'month'])),
            'strongest_season': str(strongest_season['season']),
            'best_window_start': _format_hour(best_window[0]),
            'best_window_end': _format_hour((best_window[0] + 3) % 24),
            'peak_hour': _format_hour(int(hourly.loc[hourly['power_kw'].idxmax(), 'hour'])),
            'summer_winter_difference_pct': round(comparison, 1),
        }

    def _enrich_dataset(self, dataset: dict[str, object]) -> dict[str, object]:
        if not dataset:
            return dataset

        enriched = dict(dataset)
        dataset_path = Path(str(enriched.get('path') or ''))

        enriched['original_columns'] = _parse_json_list(enriched.get('original_columns'))
        enriched['internal_columns'] = _parse_json_list(enriched.get('internal_columns'))

        if dataset_path and not enriched.get('source_name'):
            enriched['source_name'] = _source_name_from_path(dataset_path)

        try:
            if dataset_path and dataset_path.exists():
                timestamps = pd.to_datetime(
                    pd.read_parquet(dataset_path, columns=['timestamp'])['timestamp'],
                    errors='coerce'
                ).dropna().sort_values()
            elif dataset_path and not dataset_path.is_absolute():
                resolved_path = Path.cwd() / dataset_path
                enriched['path'] = resolved_path.relative_to(Path.cwd()).as_posix()
                enriched['source_name'] = _source_name_from_path(resolved_path)
                timestamps = pd.to_datetime(
                    pd.read_parquet(resolved_path, columns=['timestamp'])['timestamp'],
                    errors='coerce'
                ).dropna().sort_values()
            else:
                timestamps = pd.Series(dtype='datetime64[ns]')

            if len(timestamps) > 0:
                enriched['period_start'] = timestamps.iloc[0].isoformat()
                enriched['period_end'] = timestamps.iloc[-1].isoformat()
        except Exception:
            enriched.setdefault('period_start', None)
            enriched.setdefault('period_end', None)

        return enriched


def _month_to_season(month: int) -> str:
    if month in {12, 1, 2}:
        return 'winter'
    if month in {3, 4, 5}:
        return 'spring'
    if month in {6, 7, 8}:
        return 'summer'
    return 'autumn'


def _month_label(month: int) -> str:
    labels = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        12: 'December',
    }
    return labels.get(month, str(month))


def _infer_interval_hours(timestamps: pd.Series) -> float:
    deltas = timestamps.sort_values().diff().dropna()

    if deltas.empty:
        return 1.0

    interval_hours = (
        deltas.dt.total_seconds().median() / 3600
    )

    if not interval_hours or interval_hours <= 0:
        return 1.0

    return float(interval_hours)


def _history_unit_from_dataset(unit: str) -> str:
    normalized = unit.strip().lower()

    if normalized == 'wh':
        return 'Wh'

    return 'kWh'


def _best_three_hour_window(hours: list[int], values: list[float]) -> tuple[int, float]:
    if len(hours) < 3:
        return (hours[0] if hours else 12, 0.0)

    best_hour = hours[0]
    best_value = float('-inf')

    for index in range(len(hours) - 2):
        total = values[index] + values[index + 1] + values[index + 2]
        if total > best_value:
            best_hour = hours[index]
            best_value = total

    return best_hour, best_value


def _format_hour(hour: int) -> str:
    return f'{int(hour):02d}:00'


def _source_name_from_path(path: Path) -> str:
    stem = path.stem
    clean_stem = re.sub(r'-[0-9a-f]{32}$', '', stem, flags=re.IGNORECASE)
    return f'{clean_stem}.csv' if clean_stem else path.name


def _parse_json_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]

    if not value:
        return []

    try:
        parsed = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return []

    if not isinstance(parsed, list):
        return []

    return [str(item) for item in parsed]
