from pydantic_ai import ModelRetry
from synesis_api.utils import run_python_code_in_container


async def execute_python_code(python_code: str):
    """
    Execute a python code block.

    Args:
        ctx: The context
        python_code: The python code to execute.
    """

    out, err = await run_python_code_in_container(python_code)

    if err:
        raise ModelRetry(f"Error executing code: {err}")

    return out
