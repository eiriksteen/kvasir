import modal
from pathlib import Path
from typing import List
from uuid import UUID

from kvasir_research.secrets import MODAL_APP_NAME, MODAL_VOLUME_NAME, MODAL_PROJECTS_DIR, SANDBOX_DOCKERFILE_PATH

app = modal.App(MODAL_APP_NAME)


def upload_files_to_volume(file_paths: List[Path]):
    vol = modal.Volume.from_name(MODAL_VOLUME_NAME, create_if_missing=True)

    with vol.batch_upload() as batch:
        for file_path in file_paths:
            batch.put_file(file_path, str(MODAL_PROJECTS_DIR / file_path.name))


def create_modal_project_sandbox(project_id: UUID):
    sandbox_image = modal.Image.from_dockerfile(str(SANDBOX_DOCKERFILE_PATH))

    with modal.enable_output():
        sb = modal.Sandbox.create(
            image=sandbox_image, app=app, name=str(project_id))

    return sb
