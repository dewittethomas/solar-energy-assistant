import json
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from core.settings import get_settings
from models.installation_configuration import (
    ApplianceConsumption,
    ConsumingActivity,
    InstallationConfigurationUpdate,
)
from models.owner import OwnerPayload


class MetadataRepository:
    def __init__(self, database_path: Path | None = None) -> None:
        settings = get_settings()
        self.database_path = database_path or settings.sqlite_db_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._schema_initialized = False

    def save_dataset(
        self,
        installation_id: str,
        dataset_hash: str,
        path: str,
        row_count: int,
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
        self._ensure_schema()
        existing = self.find_dataset_by_hash(dataset_hash)

        if existing:
            existing['already_exists'] = True
            return existing

        dataset_id = self._new_id()
        created_at = self._now()
        owner_id = self._get_owner_id_for_installation(installation_id)
        self._execute(
            """
            INSERT INTO datasets (
                id,
                owner_id,
                installation_id,
                dataset_hash,
                path,
                row_count,
                granularity,
                value_column,
                production_unit,
                source_name,
                original_columns,
                internal_columns,
                date_column,
                time_column,
                measurement_column,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dataset_id,
                owner_id,
                installation_id,
                dataset_hash,
                path,
                row_count,
                granularity,
                value_column,
                production_unit,
                source_name,
                json.dumps(original_columns or []),
                json.dumps(internal_columns or []),
                date_column,
                time_column,
                measurement_column,
                created_at,
            ),
        )

        return {
            'id': dataset_id,
            'owner_id': owner_id,
            'installation_id': installation_id,
            'dataset_hash': dataset_hash,
            'path': path,
            'row_count': row_count,
            'granularity': granularity,
            'value_column': value_column,
            'production_unit': production_unit,
            'source_name': source_name,
            'original_columns': original_columns or [],
            'internal_columns': internal_columns or [],
            'date_column': date_column,
            'time_column': time_column,
            'measurement_column': measurement_column,
            'created_at': created_at,
            'already_exists': False,
        }

    def find_dataset_by_hash(self, dataset_hash: str) -> dict[str, object] | None:
        self._ensure_schema()
        return self._fetch_one(
            'SELECT * FROM datasets WHERE dataset_hash = ?',
            (dataset_hash,),
        )

    def find_dataset_by_path(self, path: str) -> dict[str, object] | None:
        self._ensure_schema()
        return self._fetch_one(
            'SELECT * FROM datasets WHERE path = ?',
            (path,),
        )

    def list_datasets(
        self,
        limit: int = 100,
        offset: int = 0,
        installation_id: str | None = None
    ) -> list[dict[str, object]]:
        self._ensure_schema()
        where_sql = ''
        parameters: tuple[object, ...] = (limit, offset)

        if installation_id is not None:
            where_sql = 'WHERE installation_id = ?'
            parameters = (installation_id, limit, offset)

        return self._fetch_all(
            f"""
            SELECT *
            FROM datasets
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            parameters,
        )

    def get_dataset(self, dataset_id: str) -> dict[str, object] | None:
        self._ensure_schema()
        return self._fetch_one(
            'SELECT * FROM datasets WHERE id = ?',
            (dataset_id,),
        )

    def get_owner(self) -> dict[str, object] | None:
        self._ensure_schema()
        owner = self._fetch_one(
            """
            SELECT *
            FROM owners
            ORDER BY created_at ASC
            LIMIT 1
            """,
            (),
        )

        if not owner:
            return None

        return self._with_owner_display_name(owner)

    def create_owner(self, owner: OwnerPayload) -> dict[str, object]:
        self._ensure_schema()

        if self.get_owner():
            raise ValueError('Local owner already exists')

        owner_id = self._new_id()
        created_at = self._now()
        updated_at = created_at
        self._execute(
            """
            INSERT INTO owners (
                id,
                first_name,
                last_name,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                owner_id,
                owner.first_name.strip(),
                self._clean_optional_text(owner.last_name),
                created_at,
                updated_at,
            ),
        )

        return self.get_owner() or {
            'id': owner_id,
            'first_name': owner.first_name.strip(),
            'last_name': self._clean_optional_text(owner.last_name),
            'created_at': created_at,
            'updated_at': updated_at,
        }

    def update_owner(self, owner: OwnerPayload) -> dict[str, object]:
        self._ensure_schema()
        existing = self.get_owner()

        if not existing:
            raise LookupError('Owner not found')

        updated_at = self._now()
        self._execute(
            """
            UPDATE owners
            SET first_name = ?,
                last_name = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                owner.first_name.strip(),
                self._clean_optional_text(owner.last_name),
                updated_at,
                str(existing['id']),
            ),
        )

        return self.get_owner() or existing

    def delete_owner(self) -> None:
        self.reset_local_state()

    def reset_local_state(self) -> None:
        self._schema_initialized = False

        if self.database_path.exists():
            self.database_path.unlink()

        settings = get_settings()

        if settings.upload_storage_dir.exists():
            shutil.rmtree(settings.upload_storage_dir, ignore_errors=True)

        if settings.model_storage_dir.exists():
            shutil.rmtree(settings.model_storage_dir, ignore_errors=True)

    def create_installation(
        self,
        owner_id: str,
        name: str,
        country: str,
        city: str,
        latitude: float,
        longitude: float,
        panel_count: int | None = None,
        capacity_kwp: float | None = None
    ) -> dict[str, object]:
        self._ensure_schema()
        installation_id = f'installation-{uuid4().hex[:8]}'
        created_at = self._now()
        is_first_installation = self._fetch_one(
            """
            SELECT id
            FROM installations
            WHERE owner_id = ?
            ORDER BY created_at ASC
            LIMIT 1
            """,
            (owner_id,),
        ) is None
        self._execute(
            """
            INSERT INTO installations (
                id,
                owner_id,
                name,
                city,
                country,
                latitude,
                longitude,
                is_active,
                panel_count,
                capacity_kwp,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                installation_id,
                owner_id,
                name.strip(),
                city.strip(),
                country.strip(),
                latitude,
                longitude,
                int(is_first_installation),
                panel_count,
                capacity_kwp,
                created_at,
            ),
        )
        self.save_installation_configuration(
            installation_id,
            InstallationConfigurationUpdate(
                name=name,
                country=country,
                city=city,
                panel_count=panel_count,
                capacity_kwp=capacity_kwp,
            ),
        )
        return self.get_installation_configuration(installation_id)

    def get_installation_configuration(
        self,
        installation_id: str
    ) -> dict[str, object]:
        self._ensure_schema()
        configuration = self._fetch_one(
            """
            SELECT
                installations.id,
                installations.id AS installation_id,
                installations.owner_id,
                installations.name,
                installations.city,
                installations.country,
                installations.latitude,
                installations.longitude,
                installations.is_active,
                installations.panel_count AS installation_panel_count,
                installations.capacity_kwp AS installation_capacity_kwp,
                installation_configurations.panel_count,
                installation_configurations.installation_kwp,
                installation_configurations.consuming_activities,
                installation_configurations.appliance_car_kwh,
                installation_configurations.appliance_washing_machine_kwh,
                installation_configurations.appliance_dishwasher_kwh,
                installation_configurations.appliance_dryer_kwh,
                installation_configurations.appliance_boiler_kwh,
                installation_configurations.updated_at
            FROM installations
            LEFT JOIN installation_configurations
                ON installation_configurations.installation_id = installations.id
            WHERE installations.id = ?
            """,
            (installation_id,),
        )

        if configuration:
            return self._format_installation_configuration(configuration)

        raise LookupError('Installation not found')

    def get_active_installation_configuration(self) -> dict[str, object] | None:
        self._ensure_schema()
        configuration = self._fetch_one(
            """
            SELECT
                installations.id,
                installations.id AS installation_id,
                installations.owner_id,
                installations.name,
                installations.city,
                installations.country,
                installations.latitude,
                installations.longitude,
                installations.is_active,
                installations.panel_count AS installation_panel_count,
                installations.capacity_kwp AS installation_capacity_kwp,
                installation_configurations.panel_count,
                installation_configurations.installation_kwp,
                installation_configurations.consuming_activities,
                installation_configurations.appliance_car_kwh,
                installation_configurations.appliance_washing_machine_kwh,
                installation_configurations.appliance_dishwasher_kwh,
                installation_configurations.appliance_dryer_kwh,
                installation_configurations.appliance_boiler_kwh,
                installation_configurations.updated_at
            FROM installations
            LEFT JOIN installation_configurations
                ON installation_configurations.installation_id = installations.id
            WHERE installations.is_active = 1
            ORDER BY installations.created_at ASC
            LIMIT 1
            """,
            (),
        )

        if not configuration:
            return None

        return self._format_installation_configuration(configuration)

    def save_installation_configuration(
        self,
        installation_id: str,
        configuration: InstallationConfigurationUpdate
    ) -> dict[str, object]:
        self._ensure_schema()
        installation = self._fetch_one(
            """
            SELECT *
            FROM installations
            WHERE id = ?
            """,
            (installation_id,),
        )

        if not installation:
            raise LookupError('Installation not found')

        existing = self._fetch_one(
            """
            SELECT *
            FROM installation_configurations
            WHERE installation_id = ?
            """,
            (installation_id,),
        )
        city = self._clean_optional_text(configuration.city) or self._clean_optional_text(
            str(installation.get('city')) if installation.get('city') is not None else None
        )
        country = self._clean_optional_text(configuration.country) or self._clean_optional_text(
            str(installation.get('country')) if installation.get('country') is not None else None
        )
        name = self._clean_optional_text(configuration.name) or self._clean_optional_text(
            str(installation.get('name')) if installation.get('name') is not None else None
        )
        latitude = installation.get('latitude')
        longitude = installation.get('longitude')
        panel_count = (
            configuration.panel_count
            if configuration.panel_count is not None
            else installation.get('panel_count')
        )
        capacity_kwp = (
            configuration.capacity_kwp
            if configuration.capacity_kwp is not None
            else installation.get('capacity_kwp')
        )

        self._execute(
            """
            UPDATE installations
            SET name = ?,
                city = ?,
                country = ?,
                latitude = ?,
                longitude = ?,
                panel_count = ?,
                capacity_kwp = ?
            WHERE id = ?
            """,
            (
                name,
                city,
                country,
                latitude,
                longitude,
                panel_count,
                capacity_kwp,
                installation_id,
            ),
        )

        updated_at = self._now()
        activities = [
            activity.model_dump()
            for activity in configuration.consuming_activities
        ]
        appliances = self._activities_to_legacy_appliances(
            configuration.consuming_activities
        )
        self._execute(
            """
            INSERT INTO installation_configurations (
                installation_id,
                city,
                panel_count,
                installation_kwp,
                consuming_activities,
                appliance_car_kwh,
                appliance_washing_machine_kwh,
                appliance_dishwasher_kwh,
                appliance_dryer_kwh,
                appliance_boiler_kwh,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(installation_id) DO UPDATE SET
                city = excluded.city,
                panel_count = excluded.panel_count,
                installation_kwp = excluded.installation_kwp,
                consuming_activities = excluded.consuming_activities,
                appliance_car_kwh = excluded.appliance_car_kwh,
                appliance_washing_machine_kwh = excluded.appliance_washing_machine_kwh,
                appliance_dishwasher_kwh = excluded.appliance_dishwasher_kwh,
                appliance_dryer_kwh = excluded.appliance_dryer_kwh,
                appliance_boiler_kwh = excluded.appliance_boiler_kwh,
                updated_at = excluded.updated_at
            """,
            (
                installation_id,
                city,
                panel_count,
                capacity_kwp,
                json.dumps(activities),
                appliances.car,
                appliances.washing_machine,
                appliances.dishwasher,
                appliances.dryer,
                appliances.boiler,
                updated_at,
            ),
        )

        return self.get_installation_configuration(installation_id)

    def list_users(self) -> list[dict[str, object]]:
        owner = self.get_owner()
        return [owner] if owner else []

    def get_user(self, user_id: str) -> dict[str, object] | None:
        owner = self.get_owner()

        if not owner or str(owner['id']) != user_id:
            return None

        return owner

    def create_training_run(
        self,
        installation_id: str,
        dataset_id: str | None = None,
        status: str = 'queued',
        phase: str = 'queued',
        progress: int = 0,
        current_trial: int | None = None,
        total_trials: int | None = None,
        best_rmse: float | None = None,
        error_code: str | None = None,
        summary: dict[str, object] | None = None
    ) -> dict[str, object]:
        self._ensure_schema()
        run_id = self._new_id()
        created_at = self._now()
        owner_id = self._get_owner_id_for_installation(installation_id)
        self._execute(
            """
            INSERT INTO training_runs (
                id,
                owner_id,
                installation_id,
                model_id,
                dataset_id,
                status,
                phase,
                progress,
                current_trial,
                total_trials,
                best_rmse,
                error_code,
                created_at,
                updated_at,
                completed_at,
                summary
            ) VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
            """,
            (
                run_id,
                owner_id,
                installation_id,
                dataset_id,
                status,
                phase,
                progress,
                current_trial,
                total_trials,
                best_rmse,
                error_code,
                created_at,
                created_at,
                json.dumps(summary) if summary else None,
            ),
        )

        return self.get_training_run(run_id) or {
            'id': run_id,
            'owner_id': owner_id,
            'installation_id': installation_id,
            'dataset_id': dataset_id,
            'status': status,
            'phase': phase,
            'progress': progress,
        }

    def start_training_run(
        self,
        dataset_id: str,
        notes: str | None = None
    ) -> dict[str, object]:
        del notes
        dataset = self.get_dataset(dataset_id)
        installation_id = (
            str(dataset['installation_id'])
            if dataset and dataset.get('installation_id')
            else 'unknown'
        )
        return self.create_training_run(
            installation_id=installation_id,
            dataset_id=dataset_id,
            status='running',
            phase='validating_dataset',
            progress=10,
        )

    def update_training_run(
        self,
        run_id: str,
        *,
        dataset_id: str | None = None,
        model_id: str | None = None,
        status: str | None = None,
        phase: str | None = None,
        progress: int | None = None,
        current_trial: int | None = None,
        total_trials: int | None = None,
        best_rmse: float | None = None,
        error_code: str | None = None,
        completed_at: str | None = None,
        summary: dict[str, object] | None = None
    ) -> None:
        self._ensure_schema()
        assignments = ['updated_at = ?']
        parameters: list[object] = [self._now()]

        for column, value in (
            ('dataset_id', dataset_id),
            ('model_id', model_id),
            ('status', status),
            ('phase', phase),
            ('progress', progress),
            ('current_trial', current_trial),
            ('total_trials', total_trials),
            ('best_rmse', best_rmse),
            ('error_code', error_code),
            ('completed_at', completed_at),
        ):
            if value is not None:
                assignments.append(f'{column} = ?')
                parameters.append(value)

        if summary is not None:
            assignments.append('summary = ?')
            parameters.append(json.dumps(summary))

        parameters.append(run_id)
        self._execute(
            f"""
            UPDATE training_runs
            SET {', '.join(assignments)}
            WHERE id = ?
            """,
            tuple(parameters),
        )

    def get_training_run(self, run_id: str) -> dict[str, object] | None:
        self._ensure_schema()
        return self._fetch_one(
            'SELECT * FROM training_runs WHERE id = ?',
            (run_id,),
        )

    def get_latest_incomplete_training_run(
        self,
        installation_id: str
    ) -> dict[str, object] | None:
        self._ensure_schema()
        return self._fetch_one(
            """
            SELECT *
            FROM training_runs
            WHERE installation_id = ?
              AND status IN ('queued', 'running')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (installation_id,),
        )

    def finish_training_run(
        self,
        run_id: str,
        status: str,
        model_id: str | None = None,
        notes: str | None = None
    ) -> None:
        del notes
        self.update_training_run(
            run_id,
            status=status,
            model_id=model_id,
            phase=status,
            progress=100 if status == 'completed' else None,
            completed_at=self._now(),
        )

    def save_model(
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
        self._ensure_schema()
        model_id = self._new_id()
        created_at = self._now()
        dataset = self.get_dataset(dataset_id)
        owner_id = (
            str(dataset['owner_id'])
            if dataset and dataset.get('owner_id')
            else self._get_owner_id_for_installation(
                str(dataset['installation_id']) if dataset else 'unknown'
            )
        )

        with self._connect() as connection:
            if is_active:
                connection.execute(
                    """
                    UPDATE models
                    SET is_active = 0
                    WHERE target_column = ?
                    AND dataset_id IN (
                        SELECT id
                        FROM datasets
                        WHERE installation_id = (
                            SELECT installation_id
                            FROM datasets
                            WHERE id = ?
                        )
                    )
                    """,
                    (target_column, dataset_id),
                )

            connection.execute(
                """
                INSERT INTO models (
                    id,
                    owner_id,
                    dataset_id,
                    version,
                    model_path,
                    is_active,
                    created_at,
                    mae,
                    rmse,
                    r2,
                    mse,
                    train_size,
                    validation_size,
                    test_size,
                    target_column
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model_id,
                    owner_id,
                    dataset_id,
                    version,
                    model_path,
                    int(is_active),
                    created_at,
                    metrics['mae'],
                    metrics['rmse'],
                    metrics['r2'],
                    metrics['mse'],
                    train_size,
                    validation_size,
                    test_size,
                    target_column,
                ),
            )

            for name, value in metrics.items():
                connection.execute(
                    """
                    INSERT INTO model_metrics (
                        id,
                        model_id,
                        metric_name,
                        metric_value,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (self._new_id(), model_id, name, value, created_at),
                )

        return {
            'id': model_id,
            'owner_id': owner_id,
            'dataset_id': dataset_id,
            'version': version,
            'model_path': model_path,
            'is_active': is_active,
            'created_at': created_at,
            **metrics,
            'train_size': train_size,
            'validation_size': validation_size,
            'test_size': test_size,
            'target_column': target_column,
        }

    def list_models(
        self,
        limit: int = 100,
        offset: int = 0,
        installation_id: str | None = None,
        is_active: bool | None = None,
        target_column: str | None = None
    ) -> list[dict[str, object]]:
        self._ensure_schema()
        where_clauses = []
        parameters: list[object] = []

        if installation_id is not None:
            where_clauses.append('datasets.installation_id = ?')
            parameters.append(installation_id)

        if is_active is not None:
            where_clauses.append('models.is_active = ?')
            parameters.append(int(is_active))

        if target_column is not None:
            where_clauses.append('models.target_column = ?')
            parameters.append(target_column)

        where_sql = (
            f"WHERE {' AND '.join(where_clauses)}"
            if where_clauses
            else ''
        )
        models = self._fetch_all(
            f"""
            SELECT models.*, datasets.installation_id, datasets.path AS dataset_path
            FROM models
            JOIN datasets ON datasets.id = models.dataset_id
            {where_sql}
            ORDER BY models.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (*parameters, limit, offset),
        )

        return [self._with_model_metrics(model) for model in models]

    def get_model(self, model_id: str) -> dict[str, object] | None:
        self._ensure_schema()
        model = self._fetch_one(
            """
            SELECT models.*, datasets.installation_id, datasets.path AS dataset_path
            FROM models
            JOIN datasets ON datasets.id = models.dataset_id
            WHERE models.id = ?
            """,
            (model_id,),
        )

        if not model:
            return None

        return self._with_model_metrics(model)

    def list_model_metrics(self, model_id: str) -> list[dict[str, object]]:
        self._ensure_schema()
        return self._fetch_all(
            """
            SELECT *
            FROM model_metrics
            WHERE model_id = ?
            ORDER BY metric_name
            """,
            (model_id,),
        )

    def activate_model(self, model_id: str) -> dict[str, object] | None:
        self._ensure_schema()
        model = self.get_model(model_id)

        if not model:
            return None

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE models
                SET is_active = 0
                WHERE dataset_id IN (
                    SELECT id
                    FROM datasets
                    WHERE installation_id = ?
                )
                """,
                (model['installation_id'],),
            )
            connection.execute(
                """
                UPDATE models
                SET is_active = 1
                WHERE id = ?
                """,
                (model_id,),
            )

        return self.get_model(model_id)

    def _ensure_schema(self) -> None:
        if self._schema_initialized:
            return

        statements = [
            """
            CREATE TABLE IF NOT EXISTS owners (
                id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS installations (
                id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                name TEXT NOT NULL,
                city TEXT NOT NULL,
                country TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                is_active INTEGER NOT NULL DEFAULT 0,
                panel_count INTEGER,
                capacity_kwp REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(owner_id) REFERENCES owners(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT,
                city TEXT NOT NULL DEFAULT '',
                installation_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS installation_configurations (
                installation_id TEXT PRIMARY KEY,
                city TEXT,
                panel_count INTEGER,
                installation_kwp REAL,
                appliance_car_kwh REAL NOT NULL DEFAULT 0,
                appliance_washing_machine_kwh REAL NOT NULL DEFAULT 0,
                appliance_dishwasher_kwh REAL NOT NULL DEFAULT 0,
                appliance_dryer_kwh REAL NOT NULL DEFAULT 0,
                appliance_boiler_kwh REAL NOT NULL DEFAULT 0,
                consuming_activities TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY,
                owner_id TEXT,
                installation_id TEXT NOT NULL,
                dataset_hash TEXT NOT NULL UNIQUE,
                path TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                granularity TEXT NOT NULL,
                value_column TEXT NOT NULL,
                production_unit TEXT,
                source_name TEXT,
                original_columns TEXT,
                internal_columns TEXT,
                date_column TEXT,
                time_column TEXT,
                measurement_column TEXT,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS models (
                id TEXT PRIMARY KEY,
                owner_id TEXT,
                dataset_id TEXT NOT NULL,
                version TEXT NOT NULL,
                model_path TEXT NOT NULL,
                is_active INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                mae REAL NOT NULL,
                rmse REAL NOT NULL,
                r2 REAL NOT NULL,
                mse REAL NOT NULL,
                train_size INTEGER NOT NULL,
                validation_size INTEGER NOT NULL,
                test_size INTEGER NOT NULL,
                target_column TEXT NOT NULL,
                FOREIGN KEY(dataset_id) REFERENCES datasets(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS training_runs (
                id TEXT PRIMARY KEY,
                owner_id TEXT,
                installation_id TEXT NOT NULL,
                model_id TEXT,
                dataset_id TEXT,
                status TEXT NOT NULL,
                phase TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                current_trial INTEGER,
                total_trials INTEGER,
                best_rmse REAL,
                error_code TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                summary TEXT,
                FOREIGN KEY(model_id) REFERENCES models(id),
                FOREIGN KEY(dataset_id) REFERENCES datasets(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS model_metrics (
                id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(model_id, metric_name),
                FOREIGN KEY(model_id) REFERENCES models(id)
            )
            """,
        ]

        with self._connect() as connection:
            for statement in statements:
                connection.execute(statement)
            self._ensure_schema_columns(connection)

        self._schema_initialized = True

    def _ensure_schema_columns(self, connection: sqlite3.Connection) -> None:
        column_statements = [
            """
            ALTER TABLE installations
            ADD COLUMN is_active INTEGER NOT NULL DEFAULT 0
            """,
            """
            ALTER TABLE datasets
            ADD COLUMN owner_id TEXT
            """,
            """
            ALTER TABLE datasets
            ADD COLUMN production_unit TEXT
            """,
            """
            ALTER TABLE datasets
            ADD COLUMN source_name TEXT
            """,
            """
            ALTER TABLE datasets
            ADD COLUMN original_columns TEXT
            """,
            """
            ALTER TABLE datasets
            ADD COLUMN internal_columns TEXT
            """,
            """
            ALTER TABLE datasets
            ADD COLUMN date_column TEXT
            """,
            """
            ALTER TABLE datasets
            ADD COLUMN time_column TEXT
            """,
            """
            ALTER TABLE datasets
            ADD COLUMN measurement_column TEXT
            """,
            """
            ALTER TABLE models
            ADD COLUMN owner_id TEXT
            """,
            """
            ALTER TABLE training_runs
            ADD COLUMN owner_id TEXT
            """,
            """
            ALTER TABLE installations
            ADD COLUMN latitude REAL
            """,
            """
            ALTER TABLE installations
            ADD COLUMN longitude REAL
            """,
            """
            ALTER TABLE installations
            ADD COLUMN panel_count INTEGER
            """,
            """
            ALTER TABLE installations
            ADD COLUMN capacity_kwp REAL
            """,
            """
            ALTER TABLE users
            ADD COLUMN city TEXT
            """,
            """
            ALTER TABLE installation_configurations
            ADD COLUMN city TEXT
            """,
            """
            ALTER TABLE training_runs
            ADD COLUMN installation_id TEXT
            """,
            """
            ALTER TABLE training_runs
            ADD COLUMN phase TEXT
            """,
            """
            ALTER TABLE training_runs
            ADD COLUMN progress INTEGER DEFAULT 0
            """,
            """
            ALTER TABLE training_runs
            ADD COLUMN current_trial INTEGER
            """,
            """
            ALTER TABLE training_runs
            ADD COLUMN total_trials INTEGER
            """,
            """
            ALTER TABLE training_runs
            ADD COLUMN best_rmse REAL
            """,
            """
            ALTER TABLE training_runs
            ADD COLUMN error_code TEXT
            """,
            """
            ALTER TABLE training_runs
            ADD COLUMN created_at TEXT
            """,
            """
            ALTER TABLE training_runs
            ADD COLUMN updated_at TEXT
            """,
            """
            ALTER TABLE training_runs
            ADD COLUMN completed_at TEXT
            """,
            """
            ALTER TABLE training_runs
            ADD COLUMN summary TEXT
            """,
        ]

        for statement in column_statements:
            try:
                connection.execute(statement)
            except sqlite3.OperationalError:
                continue

        settings = get_settings()
        fallback_city = self._clean_optional_text(settings.location) or 'Unknown'
        connection.execute(
            """
            UPDATE users
            SET city = COALESCE(NULLIF(TRIM(city), ''), ?)
            """,
            (fallback_city,),
        )
        connection.execute(
            """
            UPDATE installation_configurations
            SET city = COALESCE(
                NULLIF(TRIM(city), ''),
                (
                    SELECT users.city
                    FROM users
                    WHERE users.installation_id = installation_configurations.installation_id
                    ORDER BY users.created_at DESC
                    LIMIT 1
                ),
                ?
            )
            """,
            (fallback_city,),
        )
        self._migrate_users_to_owners(connection)
        self._migrate_configurations_to_installations(connection, fallback_city)
        connection.execute(
            """
            UPDATE installations
            SET is_active = CASE
                WHEN id = (
                    SELECT first_installation.id
                    FROM installations AS first_installation
                    WHERE first_installation.owner_id = installations.owner_id
                    ORDER BY first_installation.created_at ASC
                    LIMIT 1
                )
                THEN 1
                ELSE COALESCE(is_active, 0)
            END
            """
        )
        connection.execute(
            """
            UPDATE datasets
            SET owner_id = COALESCE(
                owner_id,
                (
                    SELECT installations.owner_id
                    FROM installations
                    WHERE installations.id = datasets.installation_id
                )
            )
            """
        )
        connection.execute(
            """
            UPDATE models
            SET owner_id = COALESCE(
                owner_id,
                (
                    SELECT datasets.owner_id
                    FROM datasets
                    WHERE datasets.id = models.dataset_id
                )
            )
            """
        )

        columns = {
            str(row['name'])
            for row in connection.execute(
                "PRAGMA table_info(training_runs)"
            ).fetchall()
        }
        started_column = 'started_at' if 'started_at' in columns else 'created_at'
        finished_column = 'finished_at' if 'finished_at' in columns else 'completed_at'

        connection.execute(
            f"""
            UPDATE training_runs
            SET created_at = COALESCE(created_at, {started_column}, ?),
                updated_at = COALESCE(updated_at, created_at, {started_column}, ?),
                completed_at = COALESCE(completed_at, {finished_column}),
                phase = COALESCE(phase, status, 'queued'),
                progress = COALESCE(progress, CASE WHEN status = 'completed' THEN 100 ELSE 0 END),
                  installation_id = COALESCE(
                    installation_id,
                    (
                        SELECT datasets.installation_id
                        FROM datasets
                        WHERE datasets.id = training_runs.dataset_id
                    ),
                      'unknown'
                  )
            """,
            (self._now(), self._now()),
        )
        connection.execute(
            """
            UPDATE training_runs
            SET owner_id = COALESCE(
                owner_id,
                (
                    SELECT datasets.owner_id
                    FROM datasets
                    WHERE datasets.id = training_runs.dataset_id
                ),
                (
                    SELECT installations.owner_id
                    FROM installations
                    WHERE installations.id = training_runs.installation_id
                )
            )
            """
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys = ON')
        return connection

    def _execute(
        self,
        query: str,
        parameters: tuple[object, ...]
    ) -> None:
        with self._connect() as connection:
            connection.execute(query, parameters)
            connection.commit()

    def _fetch_one(
        self,
        query: str,
        parameters: tuple[object, ...]
    ) -> dict[str, object] | None:
        with self._connect() as connection:
            row = connection.execute(query, parameters).fetchone()

        return self._normalize_row(row) if row else None

    def _fetch_all(
        self,
        query: str,
        parameters: tuple[object, ...] = ()
    ) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [self._normalize_row(row) for row in rows]

    def _normalize_row(self, row: sqlite3.Row | dict[str, object]) -> dict[str, object]:
        normalized = dict(row)

        if 'is_active' in normalized:
            normalized['is_active'] = bool(normalized['is_active'])

        if normalized.get('summary'):
            normalized['summary'] = json.loads(str(normalized['summary']))

        return normalized

    def _with_model_metrics(self, model: dict[str, object]) -> dict[str, object]:
        metrics = self.list_model_metrics(str(model['id']))
        model['metrics'] = {
            str(metric['metric_name']): float(metric['metric_value'])
            for metric in metrics
        }
        model['name'] = self._build_model_name(model)
        model['model_name'] = model['name']
        model['accuracy'] = self._calculate_accuracy(model)
        model['offset_kw'] = self._calculate_offset_kw(model)
        return model

    def _with_owner_display_name(
        self,
        owner: dict[str, object]
    ) -> dict[str, object]:
        display_name = str(owner['first_name'])

        if owner.get('last_name'):
            display_name = f"{display_name} {owner['last_name']}"

        owner['display_name'] = display_name
        return owner

    def _format_installation_configuration(
        self,
        row: dict[str, object]
    ) -> dict[str, object]:
        return {
            'id': str(row['id']),
            'owner_id': str(row['owner_id']),
            'installation_id': str(row['installation_id']),
            'is_active': (
                bool(row['is_active']) if row.get('is_active') is not None else None
            ),
            'name': self._clean_optional_text(row.get('name')),
            'country': self._clean_optional_text(row.get('country')),
            'city': self._clean_optional_text(row.get('city')),
            'latitude': (
                float(row['latitude']) if row.get('latitude') is not None else None
            ),
            'longitude': (
                float(row['longitude']) if row.get('longitude') is not None else None
            ),
            'panel_count': (
                row.get('panel_count')
                if row.get('panel_count') is not None
                else row.get('installation_panel_count')
            ),
            'capacity_kwp': (
                row.get('installation_kwp')
                if row.get('installation_kwp') is not None
                else row.get('installation_capacity_kwp')
            ),
            'consuming_activities': self._format_consuming_activities(row),
            'appliances': {
                'car': float(row.get('appliance_car_kwh') or 0),
                'washing_machine': float(row.get('appliance_washing_machine_kwh') or 0),
                'dishwasher': float(row.get('appliance_dishwasher_kwh') or 0),
                'dryer': float(row.get('appliance_dryer_kwh') or 0),
                'boiler': float(row.get('appliance_boiler_kwh') or 0),
            },
        }

    def _format_consuming_activities(
        self,
        row: dict[str, object]
    ) -> list[dict[str, object]]:
        raw_activities = row.get('consuming_activities') or '[]'
        activities = json.loads(raw_activities)

        if activities:
            return [
                {
                    'id': activity.get('id'),
                    'name': str(activity['name']),
                    'consumption_kwh': float(activity['consumption_kwh']),
                    'duration_minutes': (
                        int(activity['duration_minutes'])
                        if activity.get('duration_minutes') is not None
                        else None
                    ),
                    'category': activity.get('category'),
                    'is_custom': bool(activity.get('is_custom', True)),
                }
                for activity in activities
            ]

        legacy_appliances = {
            'car': float(row.get('appliance_car_kwh') or 0),
            'washing_machine': float(row.get('appliance_washing_machine_kwh') or 0),
            'dishwasher': float(row.get('appliance_dishwasher_kwh') or 0),
            'dryer': float(row.get('appliance_dryer_kwh') or 0),
            'boiler': float(row.get('appliance_boiler_kwh') or 0),
        }

        return [
            {
                'id': name,
                'name': name,
                'consumption_kwh': consumption_kwh,
                'category': 'legacy',
                'is_custom': False,
            }
            for name, consumption_kwh in legacy_appliances.items()
            if consumption_kwh > 0
        ]

    def _activities_to_legacy_appliances(
        self,
        activities: list[ConsumingActivity]
    ) -> ApplianceConsumption:
        values = {
            'car': 0,
            'washing_machine': 0,
            'dishwasher': 0,
            'dryer': 0,
            'boiler': 0,
        }

        for activity in activities:
            key = activity.name.strip().lower().replace(' ', '_').replace('-', '_')

            if key in values:
                values[key] = activity.consumption_kwh

        return ApplianceConsumption(**values)

    def update_installation_coordinates(
        self,
        installation_id: str,
        latitude: float,
        longitude: float
    ) -> None:
        self._ensure_schema()
        self._execute(
            """
            UPDATE installations
            SET latitude = ?,
                longitude = ?
            WHERE id = ?
            """,
            (latitude, longitude, installation_id),
        )

    def _migrate_users_to_owners(self, connection: sqlite3.Connection) -> None:
        owner_count = connection.execute(
            'SELECT COUNT(*) FROM owners'
        ).fetchone()[0]

        if owner_count > 0:
            return

        legacy_user = connection.execute(
            """
            SELECT *
            FROM users
            ORDER BY created_at ASC
            LIMIT 1
            """
        ).fetchone()

        if legacy_user is None:
            return

        created_at = str(legacy_user['created_at'])
        connection.execute(
            """
            INSERT INTO owners (
                id,
                first_name,
                last_name,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                self._new_id(),
                str(legacy_user['first_name']),
                self._clean_optional_text(legacy_user['last_name']),
                created_at,
                created_at,
            ),
        )

    def _migrate_configurations_to_installations(
        self,
        connection: sqlite3.Connection,
        fallback_city: str
    ) -> None:
        owner = connection.execute(
            """
            SELECT *
            FROM owners
            ORDER BY created_at ASC
            LIMIT 1
            """
        ).fetchone()

        if owner is None:
            return

        legacy_rows = connection.execute(
            """
            SELECT installation_configurations.*, users.city AS user_city
            FROM installation_configurations
            LEFT JOIN users
                ON users.installation_id = installation_configurations.installation_id
            """
        ).fetchall()

        for row in legacy_rows:
            installation_id = str(row['installation_id'])
            exists = connection.execute(
                'SELECT 1 FROM installations WHERE id = ?',
                (installation_id,),
            ).fetchone()

            if exists:
                continue

            city = self._clean_optional_text(row['city']) or self._clean_optional_text(
                row['user_city']
            ) or fallback_city
            created_at = str(row['updated_at'])
            connection.execute(
                """
                INSERT INTO installations (
                    id,
                    owner_id,
                    name,
                    city,
                    country,
                    latitude,
                    longitude,
                    panel_count,
                    capacity_kwp,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?)
                """,
                (
                    installation_id,
                    str(owner['id']),
                    'Home Installation',
                    city,
                    'Belgium',
                    row['panel_count'],
                    row['installation_kwp'],
                    created_at,
                ),
            )

    def _get_owner_id_for_installation(self, installation_id: str) -> str | None:
        installation = self._fetch_one(
            """
            SELECT owner_id
            FROM installations
            WHERE id = ?
            """,
            (installation_id,),
        )

        if installation and installation.get('owner_id'):
            return str(installation['owner_id'])

        owner = self.get_owner()
        return str(owner['id']) if owner else None

    def _build_model_name(self, model: dict[str, object]) -> str:
        return f"{model.get('target_column', 'model')} {model.get('version')}"

    def _calculate_accuracy(self, model: dict[str, object]) -> float | None:
        if model.get('r2') is None:
            return None

        return round(max(0.0, min(1.0, float(model['r2']))), 4)

    def _calculate_offset_kw(self, model: dict[str, object]) -> float | None:
        if model.get('mae') is None:
            return None

        return round(float(model['mae']) / 1000, 4)

    def _clean_optional_text(self, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    def _build_user_installation_id(self, value: str | None) -> str:
        cleaned = self._clean_optional_text(value)
        return cleaned or f'installation-{uuid4().hex[:8]}'

    def _new_id(self) -> str:
        return str(uuid4())

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()
