import uuid
from pathlib import Path
from typing import Optional, List

from project_server.agents.swe.agent import swe_agent
# from project_server.utils.agent_utils import get_folder_structure_description
from project_server.agents.swe.deps import SWEAgentDeps
from project_server.agents.swe.output import submit_implementation_output
from project_server.agents.extraction.runner import ExtractionAgentRunner
from project_server.client import get_project
from project_server.agents.runner_base import RunnerBase
from project_server.worker import broker
from project_server.utils.docker_utils import (
    write_file_to_container,
    remove_from_container,
    rename_in_container
)
# from project_server.agents.extraction.runner import ExtractionAgentRunner
# from project_server.agents.extraction.tools import extraction_toolset
from synesis_schemas.project_server import RunSWERequest, ImplementationSummary


class SWEAgentRunner(RunnerBase):

    def __init__(
            self,
            user_id: str,
            bearer_token: str,
            project_id: uuid.UUID,
            target_pipeline_id: Optional[uuid.UUID] = None,
            conversation_id: Optional[uuid.UUID] = None,
            run_id: Optional[uuid.UUID] = None,
            log: bool = False,
            input_data_source_ids: Optional[List[uuid.UUID]] = None,
            input_dataset_ids: Optional[List[uuid.UUID]] = None,
            input_analysis_ids: Optional[List[uuid.UUID]] = None,
            input_model_entity_ids: Optional[List[uuid.UUID]] = None,
            input_pipeline_ids: Optional[List[uuid.UUID]] = None,
    ):

        super().__init__(
            agent=swe_agent,
            user_id=user_id,
            bearer_token=bearer_token,
            run_id=run_id,
            run_type="swe",
            conversation_id=conversation_id,
            project_id=project_id,
        )

        self.log = log
        self.container_name = str(project_id)
        self.target_pipeline_id = target_pipeline_id

        self.input_data_source_ids = input_data_source_ids or []
        self.input_dataset_ids = input_dataset_ids or []
        self.input_analysis_ids = input_analysis_ids or []
        self.input_model_entity_ids = input_model_entity_ids or []
        self.input_pipeline_ids = input_pipeline_ids or []

        self.deps = None

        self.extraction_runner = ExtractionAgentRunner(
            user_id=user_id,
            run_id=run_id,
            bearer_token=bearer_token,
            project_id=project_id,
        )

    async def __call__(self, prompt_content: str) -> ImplementationSummary:

        try:
            await self._prepare_deps()
            await self._setup_project_container()
            await self._create_run_if_not_exists()

            run_result = await self._run_agent(
                prompt_content,
                output_type=submit_implementation_output,
                deps=self.deps
            )

            await self._log_message(
                content=f"Implementation completed, now extracting entities",
                type="result"
            )

            extraction_prompt = (
                f"The SWE agent just completed a run to create a pipeline with the ID: {self.target_pipeline_id}\n" +
                "This must be the entity_id for the pipeline entity! We don'w want a new pipeline entity, we want to add an implementation to this one!\n" +
                "Add the output pipeline implementation (include the ID in the description), data source(s),  dataset(s) of the pipeline, if there are any.\n" +
                "Do add datasets aggregating the related output data sources if any.\n" +
                "Add also any missing edges showing the data flows.\n" +
                "This includes edges to existing entities, for example the input data to the pipeline!\n" +
                f"Here is a summary of all the code created::\n\n<begin_code_summary>\n{run_result.output}\n</begin_code_summary>\n" +
                "All information necesary to create the entities should be in the code summary and visible through any new data files that have appeared.\n" +
                "As speed is crucial, submit the entities directly! No need for exploration as we have it all in the code summary."
            )

            async def complete_run():
                await self._complete_agent_run("SWE agent run completed")

            extraction_runner = ExtractionAgentRunner(
                user_id=self.user_id,
                bearer_token=self.bearer_token,
                project_id=self.project_id,
                initial_submission_callback=complete_run
            )

            await extraction_runner(prompt_content=extraction_prompt)

            return run_result.output

        except Exception as e:
            await self._revert_changes()
            await self._fail_agent_run(f"Error running SWE agent: {e}")
            raise e

    async def _prepare_deps(self) -> None:
        self.project = await get_project(self.project_client, self.project_id)

        self.deps = SWEAgentDeps(
            container_name=self.container_name,
            bearer_token=self.bearer_token,
            client=self.project_client,
            project=self.project,
            data_sources_injected=self.input_data_source_ids,
            datasets_injected=self.input_dataset_ids,
            analyses_injected=self.input_analysis_ids,
            model_instantiatedies_injected=self.input_model_entity_ids,
            pipelines_injected=self.input_pipeline_ids,
            conversation_id=self.conversation_id,
        )

    async def _revert_changes(self) -> None:
        if self.deps is None:
            return

        # Revert renamed files (rename back from new_path to old_path)
        for renamed_file in self.deps.renamed_files:
            await rename_in_container(
                Path(renamed_file.new_path),
                Path(renamed_file.old_path),
                container_name=self.container_name
            )

        # Remove new files
        for file_info in self.deps.new_files:
            await remove_from_container(
                Path(file_info.path),
                container_name=self.container_name
            )

        # Restore modified files to their original content
        for file_info in self.deps.modified_files:
            if file_info.old_content is not None:
                await write_file_to_container(
                    Path(file_info.path),
                    file_info.old_content,
                    container_name=self.container_name
                )
            else:
                raise RuntimeError(
                    f"No old_content available for modified file {file_info.path}")

        # Recreate deleted files
        for file_info in self.deps.deleted_files:
            await write_file_to_container(
                Path(file_info.path),
                file_info.content,
                container_name=self.container_name
            )


@broker.task
async def run_swe_task(
    user_id: uuid.UUID,
    bearer_token: str,
    swe_request: RunSWERequest
):
    runner = SWEAgentRunner(
        user_id=user_id,
        bearer_token=bearer_token,
        project_id=swe_request.project_id,
        conversation_id=swe_request.conversation_id,
        target_pipeline_id=swe_request.target_pipeline_id,
        run_id=swe_request.run_id,
        input_data_source_ids=swe_request.input_data_source_ids,
        input_dataset_ids=swe_request.input_dataset_ids,
        input_analysis_ids=swe_request.input_analysis_ids,
        input_model_entity_ids=swe_request.input_model_entity_ids,
        input_pipeline_ids=swe_request.input_pipeline_ids
    )

    await runner(swe_request.prompt_content)
