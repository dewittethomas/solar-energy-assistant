from pathlib import Path
import pandas as pd

from models.column_mapping import ColumnMapping
from responses.model_training_result import ModelTrainingResult
from services.preprocessing_service import PreprocessingService
from services.training_service import TrainingService

class CsvPreprocessingPipeline:
    def __init__(
        self,
        preprocessing_service: PreprocessingService | None = None
    ) -> None:
        self._preprocessing_service = (
            preprocessing_service or PreprocessingService()
        )

    def read_csv(self, file: Path):
        return self._preprocessing_service.read_csv(file)

    def get_csv_columns(self, file: Path) -> list[str]:
        return self._preprocessing_service.get_columns(file)

    def canonicalize_csv(
        self,
        file: Path,
        installation_id: str,
        mapping: ColumnMapping | dict[str, object]
    ) -> pd.DataFrame:
        return self._preprocessing_service.canonicalize_csv(
            file,
            installation_id,
            mapping
        )

    def canonicalize_csv_files(
        self,
        files: list[Path],
        installation_id: str,
        mapping: ColumnMapping | dict[str, object]
    ) -> pd.DataFrame:
        return self._preprocessing_service.canonicalize_csv_files(
            files,
            installation_id,
            mapping
        )

    def save_parquet(
        self,
        df: pd.DataFrame,
        output_path: Path
    ) -> Path:
        return self._preprocessing_service.save_parquet(df, output_path)

    def canonicalize_csv_to_parquet(
        self,
        file: Path,
        installation_id: str,
        mapping: ColumnMapping | dict[str, object],
        output_path: Path
    ) -> Path:
        return self._preprocessing_service.canonicalize_csv_to_parquet(
            file,
            installation_id,
            mapping,
            output_path
        )

    def detect_time_resolution(
        self,
        df: pd.DataFrame
    ) -> dict[str, float | str | None]:
        return self._preprocessing_service.detect_time_resolution(df)

    def resample_to_hourly(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._preprocessing_service.resample_to_hourly(df)

class ModelTrainingPipeline:
    def __init__(
        self,
        training_service: TrainingService
    ) -> None:
        self._training_service = training_service

    def train_model_from_parquet(
        self,
        parquet_path: Path,
        optimize: bool = False,
        n_trials: int = 50,
        activate_model: bool = False
    ) -> ModelTrainingResult:
        return self._training_service.train_from_parquet(
            parquet_path=parquet_path,
            optimize=optimize,
            n_trials=n_trials,
            activate_model=activate_model
        )

_pipeline = CsvPreprocessingPipeline()

def read_csv(file: Path):
    return _pipeline.read_csv(file)

def get_csv_columns(file: Path) -> list[str]:
    return _pipeline.get_csv_columns(file)

def canonicalize_csv(
    file: Path,
    installation_id: str,
    mapping: ColumnMapping | dict[str, object]
) -> pd.DataFrame:
    return _pipeline.canonicalize_csv(file, installation_id, mapping)

def canonicalize_csv_files(
    files: list[Path],
    installation_id: str,
    mapping: ColumnMapping | dict[str, object]
) -> pd.DataFrame:
    return _pipeline.canonicalize_csv_files(files, installation_id, mapping)

def save_parquet(
    df: pd.DataFrame,
    output_path: Path
) -> Path:
    return _pipeline.save_parquet(df, output_path)

def canonicalize_csv_to_parquet(
    file: Path,
    installation_id: str,
    mapping: ColumnMapping | dict[str, object],
    output_path: Path
) -> Path:
    return _pipeline.canonicalize_csv_to_parquet(
        file,
        installation_id,
        mapping,
        output_path
    )

def detect_time_resolution(df: pd.DataFrame) -> dict[str, float | str | None]:
    return _pipeline.detect_time_resolution(df)

def resample_to_hourly(df: pd.DataFrame) -> pd.DataFrame:
    return _pipeline.resample_to_hourly(df)
