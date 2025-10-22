import json
from pathlib import Path

from synesis_data_interface.sources.key_value_file.raw import KeyValueFileSource


def load_key_value_file_source(file_path: Path | str) -> KeyValueFileSource:

    file_path = Path(file_path)  # in case it is a string

    if file_path.suffix == ".json":
        with open(file_path, 'r') as f:
            data = json.load(f)
    elif file_path.suffix == ".jsonl":
        with open(file_path, 'r') as f:
            data = json.load(f, lines=True)
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

    return KeyValueFileSource(file_path, data)
