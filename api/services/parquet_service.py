from pathlib import Path

import pandas as pd

from repositories.parquet_repository import ParquetRepository

class ParquetService:
    def __init__(
        self,
        repository: ParquetRepository | None = None
    ) -> None:
        self.repository = repository or ParquetRepository()

    def save_dataframe(
        self,
        df: pd.DataFrame,
        output_path: Path
    ) -> Path:
        return self.repository.write(df, output_path)
