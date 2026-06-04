import hashlib
from pathlib import Path

import pandas as pd

from repositories.metadata_repository import MetadataRepository

class MetadataService:
    def __init__(
        self,
        repository: MetadataRepository | None = None
    ) -> None:
        self.repository = repository or MetadataRepository()

    def register_dataset(
        self,
        df: pd.DataFrame,
        installation_id: str,
        path: Path,
        granularity: str,
        value_column: str,
        production_unit: str | None = None,
        source_name: str | None = None,
        original_columns: list[str] | None = None,
        internal_columns: list[str] | None = None,
        date_column: str | None = None,
        time_column: str | None = None,
        measurement_column: str | None = None,
    ) -> dict[str, object]:
        return self.repository.save_dataset(
            installation_id=installation_id,
            dataset_hash=self.calculate_dataset_hash(df),
            path=self._format_path(path),
            row_count=len(df),
            granularity=granularity,
            value_column=value_column,
            production_unit=production_unit,
            source_name=source_name,
            original_columns=original_columns,
            internal_columns=internal_columns,
            date_column=date_column,
            time_column=time_column,
            measurement_column=measurement_column,
        )

    def register_parquet_dataset(self, path: Path) -> dict[str, object]:
        if not path.exists():
            raise ValueError(f'Parquet file does not exist: {path}')

        df = pd.read_parquet(path)

        return self.register_dataset(
            df=df,
            installation_id=self._get_installation_id(df),
            path=path,
            granularity=self._detect_granularity(df),
            value_column=self._get_value_column(df),
            production_unit='kW'
        )

    def inspect_parquet_dataset(self, path: Path) -> dict[str, object]:
        if not path.exists():
            raise ValueError(f'Parquet file does not exist: {path}')

        df = pd.read_parquet(path)
        timestamps = pd.to_datetime(df.get('timestamp'), errors='coerce')
        timestamps = timestamps.dropna().sort_values()

        return {
            'installation_id': self._get_installation_id(df),
            'dataset_hash': self.calculate_dataset_hash(df),
            'records': len(df),
            'period_start': (
                timestamps.iloc[0].date().isoformat()
                if len(timestamps) > 0
                else None
            ),
            'period_end': (
                timestamps.iloc[-1].date().isoformat()
                if len(timestamps) > 0
                else None
            ),
        }

    def list_datasets(
        self,
        limit: int = 100,
        offset: int = 0,
        installation_id: str | None = None
    ) -> list[dict[str, object]]:
        return self.repository.list_datasets(limit, offset, installation_id)

    def get_dataset(self, dataset_id: str) -> dict[str, object] | None:
        return self.repository.get_dataset(dataset_id)

    def start_training_run(
        self,
        dataset_id: str,
        notes: str | None = None
    ) -> dict[str, object]:
        return self.repository.start_training_run(dataset_id, notes)

    def create_training_run(
        self,
        installation_id: str,
        dataset_id: str | None = None,
        status: str = 'queued',
        phase: str = 'queued',
        progress: int = 0
    ) -> dict[str, object]:
        return self.repository.create_training_run(
            installation_id=installation_id,
            dataset_id=dataset_id,
            status=status,
            phase=phase,
            progress=progress,
        )

    def update_training_run(
        self,
        run_id: str,
        **changes: object
    ) -> None:
        self.repository.update_training_run(run_id, **changes)

    def get_training_run(self, run_id: str) -> dict[str, object] | None:
        return self.repository.get_training_run(run_id)

    def get_latest_incomplete_training_run(
        self,
        installation_id: str
    ) -> dict[str, object] | None:
        return self.repository.get_latest_incomplete_training_run(
            installation_id
        )

    def finish_training_run(
        self,
        run_id: str,
        status: str,
        model_id: str | None = None,
        notes: str | None = None
    ) -> None:
        self.repository.finish_training_run(run_id, status, model_id, notes)

    def register_model(
        self,
        dataset_id: str,
        version: str,
        model_path: str,
        is_active: bool,
        metrics: dict[str, float],
        train_size: int,
        validation_size: int,
        test_size: int,
        target_column: str
    ) -> dict[str, object]:
        return self.repository.save_model(
            dataset_id=dataset_id,
            version=version,
            model_path=model_path,
            is_active=is_active,
            metrics=metrics,
            train_size=train_size,
            validation_size=validation_size,
            test_size=test_size,
            target_column=target_column
        )

    def list_models(
        self,
        limit: int = 100,
        offset: int = 0,
        installation_id: str | None = None,
        is_active: bool | None = None,
        target_column: str | None = None
    ) -> list[dict[str, object]]:
        return self.repository.list_models(
            limit=limit,
            offset=offset,
            installation_id=installation_id,
            is_active=is_active,
            target_column=target_column
        )

    def get_model(self, model_id: str) -> dict[str, object] | None:
        return self.repository.get_model(model_id)

    def calculate_dataset_hash(self, df: pd.DataFrame) -> str:
        source = df.copy().reset_index(drop=True)

        for column in source.columns:
            if pd.api.types.is_datetime64_any_dtype(source[column]):
                source[column] = source[column].dt.strftime('%Y-%m-%dT%H:%M:%S')

        sort_columns = [
            column
            for column in ('installation_id', 'timestamp')
            if column in source.columns
        ]

        if sort_columns:
            source = source.sort_values(sort_columns)

        payload = source.to_csv(
            index=False,
            lineterminator='\n',
            float_format='%.12g'
        )

        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def _get_installation_id(self, df: pd.DataFrame) -> str:
        if 'installation_id' not in df.columns or df.empty:
            return 'unknown'

        installation_ids = df['installation_id'].dropna().astype(str).unique()

        if len(installation_ids) == 0:
            return 'unknown'

        if len(installation_ids) > 1:
            return 'multiple'

        return installation_ids[0]

    def _get_value_column(self, df: pd.DataFrame) -> str:
        value_columns = [
            column
            for column in ('power_kw',)
            if column in df.columns
        ]

        if len(value_columns) != 1:
            raise ValueError(
                'Expected exactly one value column: power_kw'
            )

        return value_columns[0]

    def _detect_granularity(self, df: pd.DataFrame) -> str:
        if 'timestamp' not in df.columns:
            return 'unknown'

        timestamps = (
            pd.to_datetime(df['timestamp'], errors='coerce')
            .dropna()
            .sort_values()
        )

        if len(timestamps) < 2:
            return 'unknown'

        interval_minutes = timestamps.diff().dropna().median().total_seconds() / 60

        if interval_minutes >= 60:
            return 'hourly'

        return 'sub_hourly'

    def _format_path(self, path: Path) -> str:
        try:
            return path.relative_to(Path.cwd()).as_posix()
        except ValueError:
            return path.as_posix()
