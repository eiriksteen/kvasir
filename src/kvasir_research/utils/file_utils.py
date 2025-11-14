from kvasir_research.utils.code_utils import run_shell_code_in_container
from kvasir_research.utils.docker_utils import get_container_working_directory, list_container_working_directory_contents


async def get_working_directory_description(container_name: str) -> str:
    pwd, err = await get_container_working_directory(container_name)
    if err:
        raise RuntimeError(f"Failed to get working directory: {err}")

    ls, err = await list_container_working_directory_contents(container_name)
    if err:
        raise RuntimeError(f"Failed to list working directory contents: {err}")

    return f"pwd out: {pwd}\n\nls out:\n{ls}\n\n"


async def get_folder_structure_description(
        container_name: str,
        path: str = "/app",
        n_levels: int = 5,
        max_lines: int = 100) -> str:
    find_cmd = f"find {path} -maxdepth {n_levels} \\( -name '__pycache__' -o -name '*.egg-info' \\) -prune -o -print 2>/dev/null | sort"

    out, err = await run_shell_code_in_container(find_cmd, container_name)

    if err:
        return f"folder structure {n_levels} levels down:\n\nError: {err}"

    if not out.strip():
        return f"folder structure {n_levels} levels down:\n\n(empty or does not exist)"

    all_paths = [line for line in out.split('\n') if line.strip()]

    leaf_paths = []
    for current_path in all_paths:
        is_parent = False
        for other_path in all_paths:
            if other_path != current_path and other_path.startswith(current_path + '/'):
                is_parent = True
                break

        if not is_parent:
            leaf_paths.append(current_path)

    was_truncated = len(leaf_paths) > max_lines

    if was_truncated:
        result_lines = leaf_paths[:max_lines]
        result = '\n'.join(result_lines)
        return f"folder structure {n_levels} levels down:\n\n{result}\n\n[truncated - output exceeded {max_lines} lines]"
    else:
        result = '\n'.join(leaf_paths)
        return f"folder structure {n_levels} levels down:\n\n{result}"
