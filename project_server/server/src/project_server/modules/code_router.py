import uuid
from typing import Annotated
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Response


from project_server.auth import TokenData, decode_token
from project_server.client import ProjectClient, get_project
from project_server.app_secrets import SANDBOX_DIR
from synesis_schemas.project_server import ProjectPath


router = APIRouter()


def _create_paths_recursive(project_path: Path) -> ProjectPath:
    project_path_obj = ProjectPath(
        path=project_path.name, is_file=project_path.is_file())

    if project_path.is_dir():
        items = sorted(project_path.iterdir(),
                       key=lambda x: (x.is_file(), x.name.lower()))
        for item in items:
            project_path_obj.sub_paths.append(_create_paths_recursive(item))

    return project_path_obj


@router.get("/codebase-tree")
async def get_codebase_tree_endpoint(
    project_id: uuid.UUID,
    token_data: Annotated[TokenData, Depends(decode_token)] = None
) -> ProjectPath:

    client = ProjectClient(bearer_token=token_data.bearer_token)
    project = await get_project(client, project_id)
    if str(project.user_id) != str(token_data.user_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    project_path = SANDBOX_DIR / str(project.id)
    root_folder = project_path / project.python_package_name
    tree = _create_paths_recursive(root_folder)

    # Return a virtual root with the contents of the project folder
    virtual_root = ProjectPath(
        path="", is_file=False, sub_paths=tree.sub_paths)
    return virtual_root


@router.get("/codebase-file")
async def get_codebase_file_endpoint(
    project_id: uuid.UUID,
    file_path: str,
    token_data: Annotated[TokenData, Depends(decode_token)] = None
):

    client = ProjectClient(bearer_token=token_data.bearer_token)
    project = await get_project(client, project_id)
    if str(project.user_id) != str(token_data.user_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    project_path = SANDBOX_DIR / \
        str(project.id) / project.python_package_name / file_path
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    with open(project_path, "r") as file:
        content = file.read()

    return Response(content=content, media_type="text/plain")
