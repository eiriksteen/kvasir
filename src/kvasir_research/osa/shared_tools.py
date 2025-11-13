from pydantic_ai import RunContext, ModelRetry

from kvasir_research.utils.code_utils import is_readable_extension, add_line_numbers_to_script, run_shell_code_in_container
from kvasir_research.secrets import READABLE_EXTENSIONS
from kvasir_research.osa.knowledge_bank import SUPPORTED_TASKS_LITERAL, get_guidelines
from kvasir_research.worker import logger


async def read_files_tool(ctx: RunContext, file_paths: list[str]) -> str:
    f"""
    Read the contents of one or more text-based files.
    Only supports common text file formats: {', '.join(READABLE_EXTENSIONS)}

    Args:
        ctx: The run context.
        file_paths: List of file paths to read (relative to /app or absolute).

    Returns:
        The file contents, formatted with clear separators between files.
    """
    assert hasattr(ctx.deps, "container_name"), "Container name is required"

    if not file_paths:
        raise ModelRetry("No file paths provided")

    results = []

    for file_path in file_paths:
        # Check if file has an allowed extension
        if not is_readable_extension(file_path):
            results.append(
                f"<begin_file file_path={file_path}>\n"
                f"ERROR: File does not have an allowed extension. Only text-based files are supported: {', '.join(sorted(READABLE_EXTENSIONS))}\n"
                f"<end_file>"
            )
            continue

        # Read file and check total line count
        shell_code = f"head -n 5000 {file_path} && wc -l < {file_path} || echo 'Error: File not found or cannot be read'"
        out, err = await run_shell_code_in_container(
            shell_code,
            container_name=ctx.deps.container_name,
        )

        if err or "Error:" in out or not out.strip():
            results.append(
                f"<begin_file file_path={file_path}>\n"
                f"ERROR: Could not read file - {err or out.strip()}\n"
                f"<end_file>"
            )
            continue

        # Extract total line count from end of output
        total_lines = len(out.split('\n'))
        out_with_line_numbers = add_line_numbers_to_script(out)

        if total_lines > 5000:
            results.append(
                f"<begin_file file_path={file_path}>\n\n{out_with_line_numbers}\n\n[TRUNCATED: Showing first 5000 of {total_lines} lines]\n\n<end_file>"
            )
        else:
            results.append(
                f"<begin_file file_path={file_path}>\n\n{out_with_line_numbers}\n\n<end_file>"
            )

    separator = "\n\n" + "=" * 80 + "\n\n"
    return separator.join(results)


async def get_guidelines_tool(task: SUPPORTED_TASKS_LITERAL) -> str:
    """
    Get guidelines for a machine learning task.
    """
    try:
        logger.info(f"Getting guidelines for task: {task}")
        return get_guidelines(task)
    except Exception as e:
        logger.error(f"Error getting guidelines: {e}")
        raise ModelRetry(f"Error getting guidelines: {e}")
