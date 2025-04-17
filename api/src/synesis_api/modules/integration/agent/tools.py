from pydantic_ai import ModelRetry
from ....utils import run_code_in_container
from .prompt import TIME_SERIES_TARGET_STRUCTURE


def get_target_structure(data_modality: str):
    """
    Get the target output structure of the data.

    Args:
        data_modality: The modality of the data to get the structure for, one of ["time_series", "tabular", "image", "text"]
    """
    assert data_modality in ["time_series", "tabular", "image", "text"]

    if data_modality == "time_series":
        return TIME_SERIES_TARGET_STRUCTURE
    else:
        raise ValueError(
            f"The target structure for {data_modality} data is not yet implemented.")


async def execute_python_code(python_code: str):
    """
    Execute a python code block.
    """
    out, err = await run_code_in_container(python_code)

    if err:
        raise ModelRetry(f"Error executing code: {err}")

    return out
