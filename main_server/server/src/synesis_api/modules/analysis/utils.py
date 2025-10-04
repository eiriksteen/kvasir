from typing import Any


def deep_exclude(data: Any, exclude_keys: set[str]) -> Any:
    """
    Recursively remove excluded keys from a nested dict/list structure.
    """
    if isinstance(data, dict):
        return {
            k: deep_exclude(v, exclude_keys)
            for k, v in data.items()
            if k not in exclude_keys
        }
    elif isinstance(data, list):
        return [deep_exclude(item, exclude_keys) for item in data]
    else:
        return data