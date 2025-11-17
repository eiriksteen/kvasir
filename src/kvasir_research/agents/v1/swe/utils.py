from pathlib import Path
from typing import Dict
from uuid import UUID
from pydantic_ai import RunContext

from kvasir_research.agents.v1.swe.deps import SWEDeps


def modified_files_to_string(modified_files: Dict[str, str], run_id: UUID, run_name: str, execution_command: str, execution_output: str) -> str:
    result = [f'<swe_result run_id="{run_id}" run_name="{run_name}">']

    if not modified_files:
        result.append("")
        result.append("  (no files modified)")
    else:
        for file_path, content in modified_files.items():
            result.append("")
            result.append(f'  <file path="{file_path}">')
            # Indent content lines
            for line in content.split("\n"):
                result.append(f"    {line}")
            result.append("  </file>")

    # Add execution command if provided
    if execution_command:
        result.append("")
        result.append(
            f'  <execution_command>{execution_command}</execution_command>')

    # Add execution output
    if execution_output:
        result.append("")
        result.append("  <execution_output>")
        for line in execution_output.split("\n"):
            result.append(f"    {line}")
        result.append("  </execution_output>")

    result.append("")
    result.append("</swe_result>")

    return "\n".join(result)


def validate_path_permissions(ctx: RunContext[SWEDeps], path: str | Path) -> bool:
    path = Path(path).resolve()

    # Check if path is in any read-only path
    for read_only_path in ctx.deps.read_only_paths:
        if ctx.deps.sandbox.is_subpath(path, Path(read_only_path).resolve()):
            return False

    return True

