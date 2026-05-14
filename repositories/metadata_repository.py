from datetime import UTC, datetime
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row

from core.settings import get_settings
from models.user import UserCreate

class MetadataRepository:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or get_settings().database_url
        self._schema_initialized = False

    def save_dataset(
        self,
        installation_id: str,
        dataset_hash: str,
        path: str,
        row_count: int,
        granularity: str,
        value_column: str
    ) -> dict[str, object]:
        self._ensure_schema()
        existing = self.find_dataset_by_hash(dataset_hash)

        if existing:
            existing['already_exists'] = True

            return existing

        dataset_id = uuid4()
        created_at = self._now()
        self._execute(
            """
            INSERT INTO datasets (
                id,
                installation_id,
                dataset_hash,
                path,
                row_count,
                granularity,
                value_column,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                dataset_id,
                installation_id,
                dataset_hash,
                path,
                row_count,
                granularity,
                value_column,
                created_at
            )
        )

        return {
            'id': str(dataset_id),
            'installation_id': installation_id,
            'dataset_hash': dataset_hash,
            'path': path,
            'row_count': row_count,
            'granularity': granularity,
            'value_column': value_column,
            'created_at': created_at.isoformat(),
            'already_exists': False
        }

    def find_dataset_by_hash(self, dataset_hash: str) -> dict[str, object] | None:
        self._ensure_schema()

        return self._fetch_one(
            'SELECT * FROM datasets WHERE dataset_hash = %s',
            (dataset_hash,)
        )

    def find_dataset_by_path(self, path: str) -> dict[str, object] | None:
        self._ensure_schema()

        return self._fetch_one(
            'SELECT * FROM datasets WHERE path = %s',
            (path,)
        )

    def list_datasets(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict[str, object]]:
        self._ensure_schema()

        return self._fetch_all(
            """
            SELECT *
            FROM datasets
            ORDER BY datasets.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset)
        )

    def get_dataset(self, dataset_id: str) -> dict[str, object] | None:
        self._ensure_schema()
        dataset_id = self._parse_uuid(dataset_id)

        if not dataset_id:
            return None

        return self._fetch_one(
            'SELECT * FROM datasets WHERE id = %s',
            (dataset_id,)
        )

    def create_user(self, user: UserCreate) -> dict[str, object]:
        self._ensure_schema()
        user_id = uuid4()
        created_at = self._now()
        first_name = user.first_name.strip()
        last_name = self._clean_optional_text(user.last_name)
        installation_id = self._build_user_installation_id(user.installation_id)
        self._execute(
            """
            INSERT INTO users (
                id,
                first_name,
                last_name,
                installation_id,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                user_id,
                first_name,
                last_name,
                installation_id,
                created_at
            )
        )

        return self._with_user_display_name({
            'id': str(user_id),
            'first_name': first_name,
            'last_name': last_name,
            'installation_id': installation_id,
            'created_at': created_at.isoformat()
        })

    def list_users(self) -> list[dict[str, object]]:
        self._ensure_schema()
        users = self._fetch_all(
            """
            SELECT *
            FROM users
            ORDER BY first_name, last_name NULLS FIRST, created_at DESC
            """
        )

        return [
            self._with_user_display_name(user)
            for user in users
        ]

    def get_user(self, user_id: str) -> dict[str, object] | None:
        self._ensure_schema()
        user_id = self._parse_uuid(user_id)

        if not user_id:
            return None

        user = self._fetch_one(
            'SELECT * FROM users WHERE id = %s',
            (user_id,)
        )

        if not user:
            return None

        return self._with_user_display_name(user)

    def start_training_run(
        self,
        dataset_id: str,
        notes: str | None = None
    ) -> dict[str, object]:
        self._ensure_schema()
        run_id = uuid4()
        started_at = self._now()
        self._execute(
            """
            INSERT INTO training_runs (
                id,
                model_id,
                dataset_id,
                status,
                started_at,
                finished_at,
                notes
            )
            VALUES (%s, NULL, %s, %s, %s, NULL, %s)
            """,
            (run_id, dataset_id, 'running', started_at, notes)
        )

        return {
            'id': str(run_id),
            'dataset_id': dataset_id,
            'status': 'running',
            'started_at': started_at.isoformat(),
            'notes': notes
        }

    def finish_training_run(
        self,
        run_id: str,
        status: str,
        model_id: str | None = None,
        notes: str | None = None
    ) -> None:
        self._ensure_schema()
        self._execute(
            """
            UPDATE training_runs
            SET status = %s,
                model_id = %s,
                finished_at = %s,
                notes = %s
            WHERE id = %s
            """,
            (status, model_id, self._now(), notes, run_id)
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
        model_id = uuid4()
        created_at = self._now()

        with self._connect() as connection:
            if is_active:
                connection.execute(
                    """
                    UPDATE models
                    SET is_active = FALSE
                    WHERE target_column = %s
                    AND dataset_id IN (
                        SELECT id
                        FROM datasets
                        WHERE installation_id = (
                            SELECT installation_id
                            FROM datasets
                            WHERE id = %s
                        )
                    )
                    """,
                    (target_column, dataset_id)
                )

            connection.execute(
                """
                INSERT INTO models (
                    id,
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
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    model_id,
                    dataset_id,
                    version,
                    model_path,
                    is_active,
                    created_at,
                    metrics['mae'],
                    metrics['rmse'],
                    metrics['r2'],
                    metrics['mse'],
                    train_size,
                    validation_size,
                    test_size,
                    target_column
                )
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
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (uuid4(), model_id, name, value, created_at)
                )

        return {
            'id': str(model_id),
            'dataset_id': dataset_id,
            'version': version,
            'model_path': model_path,
            'is_active': is_active,
            'created_at': created_at.isoformat(),
            **metrics,
            'train_size': train_size,
            'validation_size': validation_size,
            'test_size': test_size,
            'target_column': target_column
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
            where_clauses.append('datasets.installation_id = %s')
            parameters.append(installation_id)

        if is_active is not None:
            where_clauses.append('models.is_active = %s')
            parameters.append(is_active)

        if target_column is not None:
            where_clauses.append('models.target_column = %s')
            parameters.append(target_column)

        where_sql = (
            f"WHERE {' AND '.join(where_clauses)}"
            if where_clauses
            else ''
        )
        models = self._fetch_all(
            f"""
            SELECT models.*, datasets.installation_id
            FROM models
            JOIN datasets ON datasets.id = models.dataset_id
            {where_sql}
            ORDER BY models.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (*parameters, limit, offset)
        )

        return [
            self._with_model_metrics(model)
            for model in models
        ]

    def get_model(self, model_id: str) -> dict[str, object] | None:
        self._ensure_schema()
        model_id = self._parse_uuid(model_id)

        if not model_id:
            return None

        model = self._fetch_one(
            """
            SELECT models.*, datasets.installation_id
            FROM models
            JOIN datasets ON datasets.id = models.dataset_id
            WHERE models.id = %s
            """,
            (model_id,)
        )

        if not model:
            return None

        return self._with_model_metrics(model)

    def list_model_metrics(self, model_id: str) -> list[dict[str, object]]:
        self._ensure_schema()
        model_id = self._parse_uuid(model_id)

        if not model_id:
            return []

        return self._fetch_all(
            """
            SELECT *
            FROM model_metrics
            WHERE model_id = %s
            ORDER BY metric_name
            """,
            (model_id,)
        )

    def _ensure_schema(self) -> None:
        if self._schema_initialized:
            return

        self._initialize_schema()
        self._schema_initialized = True

    def _initialize_schema(self) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT,
                installation_id TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS datasets (
                id UUID PRIMARY KEY,
                installation_id TEXT NOT NULL,
                dataset_hash TEXT NOT NULL UNIQUE,
                path TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                granularity TEXT NOT NULL,
                value_column TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS models (
                id UUID PRIMARY KEY,
                dataset_id UUID NOT NULL REFERENCES datasets(id),
                version TEXT NOT NULL,
                model_path TEXT NOT NULL,
                is_active BOOLEAN NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                mae DOUBLE PRECISION NOT NULL,
                rmse DOUBLE PRECISION NOT NULL,
                r2 DOUBLE PRECISION NOT NULL,
                mse DOUBLE PRECISION NOT NULL,
                train_size INTEGER NOT NULL,
                validation_size INTEGER NOT NULL,
                test_size INTEGER NOT NULL,
                target_column TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS training_runs (
                id UUID PRIMARY KEY,
                model_id UUID REFERENCES models(id),
                dataset_id UUID NOT NULL REFERENCES datasets(id),
                status TEXT NOT NULL,
                started_at TIMESTAMPTZ NOT NULL,
                finished_at TIMESTAMPTZ,
                notes TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS model_metrics (
                id UUID PRIMARY KEY,
                model_id UUID NOT NULL REFERENCES models(id),
                metric_name TEXT NOT NULL,
                metric_value DOUBLE PRECISION NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                UNIQUE(model_id, metric_name)
            )
            """
        ]

        with self._connect() as connection:
            for statement in statements:
                connection.execute(statement)

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def _execute(self, query: str, parameters: tuple[object, ...]) -> None:
        with self._connect() as connection:
            connection.execute(query, parameters)

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

        return [
            self._normalize_row(row)
            for row in rows
        ]

    def _with_model_metrics(
        self,
        model: dict[str, object]
    ) -> dict[str, object]:
        metrics = self.list_model_metrics(str(model['id']))
        model['metrics'] = {
            str(metric['metric_name']): float(metric['metric_value'])
            for metric in metrics
        }

        return model

    def _with_user_display_name(
        self,
        user: dict[str, object]
    ) -> dict[str, object]:
        display_name = str(user['first_name'])

        if user.get('last_name'):
            display_name = f"{display_name} {user['last_name']}"

        user['display_name'] = display_name

        return user

    def _clean_optional_text(self, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None

    def _build_user_installation_id(self, value: str | None) -> str:
        cleaned = self._clean_optional_text(value)

        return cleaned or f'installation-{uuid4().hex[:8]}'

    def _parse_uuid(self, value: str) -> UUID | None:
        try:
            return UUID(str(value))
        except ValueError:
            return None

    def _normalize_row(self, row: dict[str, object]) -> dict[str, object]:
        normalized = dict(row)

        for key, value in normalized.items():
            if isinstance(value, UUID):
                normalized[key] = str(value)
            elif isinstance(value, datetime):
                normalized[key] = value.isoformat()

        return normalized

    def _now(self) -> datetime:
        return datetime.now(UTC)
