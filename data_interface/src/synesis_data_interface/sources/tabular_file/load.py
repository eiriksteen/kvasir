import pandas as pd
from pathlib import Path

from synesis_data_interface.sources.tabular_file.raw import TabularFileSource


def load_tabular_file_source(file_path: Path | str) -> TabularFileSource:

    file_path = Path(file_path)  # in case it is a string

    if file_path.suffix == ".csv":
        df = pd.read_csv(file_path)
    elif file_path.suffix == ".parquet":
        df = pd.read_parquet(file_path)
    elif file_path.suffix == ".json":
        df = pd.read_json(file_path)
    elif file_path.suffix == ".jsonl":
        df = pd.read_json(file_path, lines=True)
    elif file_path.suffix == ".xlsx":
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

    return TabularFileSource(file_path, df)
