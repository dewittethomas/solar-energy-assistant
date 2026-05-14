import re

import pandas as pd

from core.settings import get_settings
from models.column_mapping import ColumnMapping


class DataFrameCanonicalizer:
    def __init__(self, timezone: str | None = None) -> None:
        self._timezone = timezone or get_settings().timezone

    def canonicalize(
        self,
        df: pd.DataFrame,
        installation_id: str,
        mapping: ColumnMapping
    ) -> pd.DataFrame:
        source = self._rename_selected_columns(df, mapping)
        timestamp = self._build_timestamp(source, has_time=bool(mapping.time_column))
        measurement = self._parse_number_series(source['measurement'])
        value_column, measurement = self._normalize_measurement(
            measurement,
            mapping.unit
        )

        canonical = pd.DataFrame({
            'installation_id': installation_id,
            'timestamp': timestamp,
            value_column: measurement
        })

        canonical = canonical.dropna(subset=['timestamp', value_column])
        canonical = canonical.drop_duplicates(
            subset=['installation_id', 'timestamp'],
            keep='last'
        )

        return canonical.sort_values('timestamp').reset_index(drop=True)

    def _rename_selected_columns(
        self,
        df: pd.DataFrame,
        mapping: ColumnMapping
    ) -> pd.DataFrame:
        selected_columns = {
            mapping.date_column: 'date',
            mapping.measurement_column: 'measurement'
        }

        if mapping.time_column:
            selected_columns[mapping.time_column] = 'time'

        missing_columns = [
            column
            for column in selected_columns
            if column not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f'Missing column(s): {", ".join(missing_columns)}'
            )

        return (
            df[list(selected_columns.keys())]
            .rename(columns=selected_columns)
            .copy()
        )

    def _build_timestamp(
        self,
        df: pd.DataFrame,
        has_time: bool
    ) -> pd.Series:
        if has_time:
            timestamp_values = (
                df['date'].astype(str).str.strip()
                + ' '
                + df['time'].astype(str).str.strip()
            )
        else:
            timestamp_values = df['date']

        return self._parse_timestamp_series(timestamp_values)

    def _parse_number_series(self, values: pd.Series) -> pd.Series:
        normalized = (
            values
            .astype(str)
            .str.strip()
            .str.replace(' ', '', regex=False)
        )

        def normalize_number(value: str) -> str:
            if value in ('', 'nan', 'None'):
                return ''

            has_comma = ',' in value
            has_dot = '.' in value

            if has_comma and has_dot:
                decimal_separator = ',' if value.rfind(',') > value.rfind('.') else '.'
                thousands_separator = '.' if decimal_separator == ',' else ','

                value = value.replace(thousands_separator, '')
                value = value.replace(decimal_separator, '.')
            elif has_comma:
                value = value.replace(',', '.')
            elif re.match(r'^-?\d{1,3}(\.\d{3})+$', value):
                value = value.replace('.', '')

            return value

        return pd.to_numeric(
            normalized.map(normalize_number),
            errors='coerce'
        )

    def _parse_timestamp_series(self, values: pd.Series) -> pd.Series:
        month_replacements = {
            'jan': 'jan',
            'januari': 'jan',
            'feb': 'feb',
            'februari': 'feb',
            'mrt': 'mar',
            'maart': 'mar',
            'mar': 'mar',
            'apr': 'apr',
            'april': 'apr',
            'mei': 'may',
            'may': 'may',
            'jun': 'jun',
            'juni': 'jun',
            'jul': 'jul',
            'juli': 'jul',
            'aug': 'aug',
            'augustus': 'aug',
            'sep': 'sep',
            'sept': 'sep',
            'september': 'sep',
            'okt': 'oct',
            'oktober': 'oct',
            'oct': 'oct',
            'october': 'oct',
            'nov': 'nov',
            'november': 'nov',
            'dec': 'dec',
            'december': 'dec',
        }

        def normalize_timestamp(value: object) -> object:
            if pd.isna(value):
                return value

            normalized = str(value).strip()
            match = re.match(r'^([A-Za-z]+)\.?\s+(\d{4})$', normalized)

            if match:
                month = month_replacements.get(match.group(1).lower())

                if month:
                    return f'1 {month} {match.group(2)}'

            return normalized

        normalized_values = values.map(normalize_timestamp)
        iso_timestamps = normalized_values.astype(str).str.match(
            r'^\d{4}-\d{2}-\d{2}'
        )
        timestamps = pd.Series(pd.NaT, index=normalized_values.index)

        timestamps.loc[iso_timestamps] = self._parse_without_timezone(
            normalized_values.loc[iso_timestamps]
        )
        timestamps.loc[~iso_timestamps] = self._parse_without_timezone(
            normalized_values.loc[~iso_timestamps],
            dayfirst=True
        )

        missing_timestamps = timestamps.isna()

        if missing_timestamps.any():
            timestamps.loc[missing_timestamps] = self._parse_without_timezone(
                normalized_values.loc[missing_timestamps]
            )

        return pd.to_datetime(timestamps)

    def _parse_without_timezone(
        self,
        values: pd.Series,
        dayfirst: bool = False
    ) -> pd.Series:
        values_as_text = values.astype(str).str.strip()
        has_timezone = values_as_text.str.contains(
            r'(?:[zZ]|[+-]\d{2}:?\d{2})$',
            regex=True,
            na=False
        )
        timestamps = pd.Series(pd.NaT, index=values.index)

        if has_timezone.any():
            timezone_aware = pd.to_datetime(
                values.loc[has_timezone],
                errors='coerce',
                dayfirst=dayfirst,
                format='mixed',
                utc=True
            )
            timestamps.loc[has_timezone] = (
                timezone_aware
                .dt.tz_convert(self._timezone)
                .dt.tz_localize(None)
            )

        if (~has_timezone).any():
            timestamps.loc[~has_timezone] = pd.to_datetime(
                values.loc[~has_timezone],
                errors='coerce',
                dayfirst=dayfirst,
                format='mixed'
            )

        return pd.to_datetime(
            timestamps,
            errors='coerce',
            dayfirst=dayfirst,
            format='mixed'
        )

    def _normalize_measurement(
        self,
        measurement: pd.Series,
        unit: str
    ) -> tuple[str, pd.Series]:
        normalized_unit = unit.strip().lower().replace(' ', '')

        if normalized_unit == 'w':
            return 'power_kw', measurement / 1000

        if normalized_unit == 'kw':
            return 'power_kw', measurement

        if normalized_unit == 'wh':
            return 'energy_kwh', measurement / 1000

        if normalized_unit == 'kwh':
            return 'energy_kwh', measurement

        raise ValueError(f'Unsupported unit: {unit}')
