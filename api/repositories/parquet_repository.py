from pathlib import Path

import pandas as pd

class ParquetRepository:
    def write(self, df: pd.DataFrame, output_path: Path) -> Path:
        output_path = output_path.with_suffix('.parquet')
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_parquet(output_path, index=False)

        return output_path
