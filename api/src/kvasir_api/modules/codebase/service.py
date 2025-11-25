from uuid import UUID
from typing import Annotated, List, Dict
from pathlib import Path
from fastapi import Depends
import shlex

from kvasir_ontology.code.data_model import CodebaseFile, CodebasePath, CodebaseFilePaginated
from kvasir_ontology.code.interface import CodeInterface
from kvasir_api.modules.entity_graph.service import EntityGraphs
from kvasir_agents.sandbox.modal import ModalSandbox
from kvasir_api.auth.service import get_current_user
from kvasir_api.auth.schema import User


def _is_likely_file(path: str) -> bool:
    path_obj = Path(path)
    return bool(path_obj.suffix)


def _parse_folder_structure_to_tree(folder_structure_output: str) -> CodebasePath:
    lines = folder_structure_output.split('\n')
    paths: List[str] = []

    for line in lines:
        line = line.strip()
        # Skip header, empty lines, and truncation message
        if (not line or
            line.startswith('folder structure') or
            line.startswith('[truncated') or
            line.startswith('Error:') or
                line == '(empty or does not exist)'):
            continue
        paths.append(line)

    if not paths:
        # Return empty root structure
        return CodebasePath(path="/", is_file=False, sub_paths=[])

    # Create root node
    root_node = CodebasePath(path="/", is_file=False, sub_paths=[])

    # Track all nodes by their full path for quick lookup
    # Key: full path string, Value: CodebasePath node
    path_nodes: Dict[str, CodebasePath] = {"/": root_node}

    def get_or_create_node(full_path: str, parent_node: CodebasePath, component_name: str, is_file: bool) -> CodebasePath:
        if full_path in path_nodes:
            return path_nodes[full_path]

        node = CodebasePath(
            path=component_name,
            is_file=is_file,
            sub_paths=[]
        )
        path_nodes[full_path] = node
        parent_node.sub_paths.append(node)
        return node

    # Process each path and create intermediate nodes
    for path_str in paths:
        # Normalize path - remove leading ./ or /
        normalized = path_str.lstrip('./')
        if not normalized:
            continue

        # Split into components
        path_obj = Path(normalized)
        components = path_obj.parts

        # Navigate/create the tree path
        current_node = root_node
        current_path = "/"

        for i, component in enumerate(components):
            # Build full path up to this component
            if current_path == "/":
                current_path = component
            else:
                current_path = f"{current_path}/{component}"

            # Determine if this is a file (only the last component can be a file)
            is_file = (i == len(components) -
                       1) and _is_likely_file(normalized)

            # Get or create the node
            current_node = get_or_create_node(
                current_path,
                current_node,
                component,
                is_file
            )

    return root_node


class Codebase(CodeInterface):

    def __init__(self, user_id: UUID, mount_group_id: UUID):
        super().__init__(user_id, mount_group_id)
        self.user_id = user_id
        self.mount_group_id = mount_group_id
        self.graph_service = EntityGraphs(user_id)

    async def get_codebase_tree(self) -> CodebasePath:
        mount_group = await self.graph_service.get_node_group(self.mount_group_id)
        sandbox = ModalSandbox(self.mount_group_id,
                               mount_group.python_package_name)

        # Get folder structure from sandbox with high depth
        folder_structure_output = await sandbox.get_folder_structure(
            path=None,  # Use working directory
            n_levels=20,  # High depth to get full structure
            max_lines=10000  # High line limit
        )

        # Parse the output into CodebasePath tree
        tree = _parse_folder_structure_to_tree(folder_structure_output)
        return tree

    async def get_codebase_file(self, file_path: str) -> CodebaseFile:
        mount_group = await self.graph_service.get_node_group(self.mount_group_id)
        sandbox = ModalSandbox(self.mount_group_id,
                               mount_group.python_package_name)

        try:
            file_content = await sandbox.read_file(file_path, truncate=False)
            return CodebaseFile(path=file_path, content=file_content)
        except Exception as e:
            raise FileNotFoundError(f"File not found: {file_path}") from e

    async def get_codebase_file_paginated(
        self,
        file_path: str,
        offset: int = 0,
        limit: int = 100
    ) -> CodebaseFilePaginated:
        """Get a paginated portion of a file's content.

        Args:
            file_path: Path to the file
            offset: Line number to start from (0-indexed)
            limit: Number of lines to return

        Returns:
            CodebaseFilePaginated with the requested lines and pagination metadata
        """
        mount_group = await self.graph_service.get_node_group(self.mount_group_id)
        sandbox = ModalSandbox(self.mount_group_id,
                               mount_group.python_package_name)

        try:
            quoted_path = shlex.quote(file_path)

            # Get total line count efficiently without reading the file
            line_count_out, line_count_err = await sandbox.run_shell_code(
                f"wc -l < {quoted_path}",
                truncate_output=False
            )

            if line_count_err:
                raise FileNotFoundError(f"File not found: {file_path}")

            total_lines = int(line_count_out.strip())

            # Calculate pagination
            start_line = offset + 1  # sed uses 1-indexed lines
            end_line = min(offset + limit, total_lines)
            has_more = end_line < total_lines

            # Read only the requested lines using sed
            if total_lines > 0 and start_line <= total_lines:
                sed_out, sed_err = await sandbox.run_shell_code(
                    f"sed -n '{start_line},{end_line}p' {quoted_path}",
                    truncate_output=False
                )

                if sed_err:
                    raise RuntimeError(f"Failed to read file lines: {sed_err}")

                paginated_content = sed_out
            else:
                paginated_content = ""

            return CodebaseFilePaginated(
                path=file_path,
                content=paginated_content,
                offset=offset,
                limit=limit,
                total_lines=total_lines,
                has_more=has_more
            )
        except Exception as e:
            raise FileNotFoundError(f"File not found: {file_path}") from e


def get_codebase_service(
    mount_group_id: UUID,
    user: Annotated[User, Depends(get_current_user)]
) -> Codebase:
    return Codebase(user.id, mount_group_id)
