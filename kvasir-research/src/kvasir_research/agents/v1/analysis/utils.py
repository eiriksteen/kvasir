from typing import Dict, Tuple
from uuid import UUID
from pathlib import Path


def notebook_to_string(notebook: Dict[str, Tuple[str, str]], run_id: UUID, run_name: str) -> str:
    if not notebook:
        return f'<analysis run_id="{run_id}" run_name="{run_name}">\n  (empty notebook)\n</analysis>'

    result = [f'<analysis run_id="{run_id}" run_name="{run_name}">']

    for cell_name, (cell_type, content) in notebook.items():
        if cell_type == "markdown":
            result.append("")
            result.append(f'  <markdown name="{cell_name}">')
            # Indent content lines
            for line in content.strip().split("\n"):
                result.append(f"    {line}")
            result.append("  </markdown>")

        elif cell_type == "code":
            result.append("")
            result.append(f'  <code name="{cell_name}">')
            # Indent code lines
            for line in content.strip().split("\n"):
                result.append(f"    {line}")
            result.append("  </code>")

        elif cell_type == "output":
            result.append("")
            result.append("  <output>")
            # Indent output lines
            for line in content.strip().split("\n"):
                result.append(f"    {line}")
            result.append("  </output>")

    result.append("")
    result.append("</analysis>")

    return "\n".join(result)
