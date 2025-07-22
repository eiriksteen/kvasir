from pathlib import Path


def list_directory_contents(data_directory: Path):
    """
    List the contents of the directory.

    Args:
        ctx: The context
    """

    all_paths = data_directory.glob("**/*")
    visible_paths = [p for p in all_paths if not any(
        part.startswith(".") for part in p.parts)]
    relative_paths = [str(p.relative_to(data_directory))
                      for p in visible_paths]

    return "\n".join(relative_paths)


def resolve_path_from_directory_name(directory_name: str, search_path: Path) -> Path:
    """
    Resolve the path from the directory name by searching through all directory names in the search_path.

    Args:
        directory_name: The name of the directory.
        search_path: The path to search through.
    """

    for path in search_path.glob("**/*"):
        if path.name == directory_name:
            return path

    raise ValueError(
        f"Directory name {directory_name} not found in {search_path}")
