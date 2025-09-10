import uuid
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel
from pydantic_ai.agent import AgentRunResult

from project_server.agents.data_source_analysis.agent import data_source_analysis_agent, DataSourceAnalysisAgentDeps
from project_server.agents.data_source_analysis.output import TabularFileAnalysisOutput, CallSWEToImplementFunctionOutput
from project_server.worker import broker, logger
from project_server.agents.swe.runner import SWEAgentRunner
from project_server.agents.data_source_analysis.prompt import DATA_SOURCE_AGENT_SYSTEM_PROMPT
from project_server.agents.swe.output import SWEAgentOutput
from project_server.client import (
    ProjectClient,
    post_data_source_analysis,
    post_data_source_details,
    post_run_message_pydantic,
    post_run,
    patch_run_status,
)
from synesis_schemas.main_server import (
    TabularFileDataSourceCreate,
    DataSourceAnalysisCreate,
    RunMessageCreatePydantic,
    RunCreate,
    RunStatusUpdate,
)


class DataSourceAnalysisRunnerOutput(BaseModel):
    source_analysis: TabularFileAnalysisOutput
    swe_outputs: List[SWEAgentOutput]


class DataSourceAnalysisRunner:

    def __init__(self, user_id: str, source_id: uuid.UUID, file_path: str, bearer_token: str, run_id: Optional[uuid.UUID] = None):
        self.data_source_agent = data_source_analysis_agent
        self.user_id = user_id
        self.source_id = source_id
        self.logger = logger
        self.run_id = run_id
        self.file_path = Path(file_path)
        self.swe_runner = SWEAgentRunner(user_id, bearer_token)
        self.bearer_token = bearer_token
        self.project_client = ProjectClient()
        self.project_client.set_bearer_token(bearer_token)

    async def _save_results(self, result: AgentRunResult):

        output: TabularFileAnalysisOutput = result.output

        await post_data_source_details(self.project_client, TabularFileDataSourceCreate(
            data_source_id=self.source_id,
            file_name=self.file_path.name,
            file_path=str(self.file_path),
            file_type=self.file_path.suffix,
            file_size_bytes=output.file_size_bytes,
            num_rows=output.num_rows,
            num_columns=output.num_columns,
        ))

        await post_data_source_analysis(self.project_client, DataSourceAnalysisCreate(
            data_source_id=self.source_id,
            content_description=output.content_description,
            quality_description=output.quality_description,
            eda_summary=output.eda_summary,
            cautions=output.cautions,
            features=output.features,
        ))

        await post_run_message_pydantic(self.project_client, RunMessageCreatePydantic(
            run_id=self.run_id,
            content=result.all_messages_json()
        ))

        await patch_run_status(self.project_client, RunStatusUpdate(
            run_id=self.run_id,
            status="completed"
        ))

        # TODO: Save the SWE functions

    async def __call__(self) -> DataSourceAnalysisRunnerOutput:

        try:
            if self.run_id is None:
                run = await post_run(self.project_client, RunCreate(type="data_source_analysis"))
                self.run_id = run.id

            deps = DataSourceAnalysisAgentDeps(file_path=self.file_path)

            run_output, message_history, swe_outputs = None, [], []

            current_prompt = (
                f"Start analyzing the data source!\n\n" +
                "Choose your action: " +
                "1. Request a function to analyze the data source\n" +
                "2. If the analysis is sufficient, output the final analysis result\n",
            )

            while not isinstance(run_output, TabularFileAnalysisOutput):

                run_result: AgentRunResult = await self.data_source_agent.run(
                    current_prompt,
                    output_type=[CallSWEToImplementFunctionOutput,
                                 TabularFileAnalysisOutput],
                    deps=deps,
                    message_history=message_history
                )

                if isinstance(run_result.output, CallSWEToImplementFunctionOutput):

                    logger.info(
                        f"Calling SWE agent to implement function: {run_result.output}")

                    deliverable_description = (
                        "I have been tasked to analyze a data source. For context, this is my full task description:\n\n" +
                        f"'{DATA_SOURCE_AGENT_SYSTEM_PROMPT}'\n\n" +
                        f"Now I need you to implement a function to analyze the data source. You need to implement:\n\n{run_result.output}\n\n" +
                        "The first argument(s) should be the key(s) to access the data source. " +
                        "For example, if the data source is a file, the first argument should be the file path. " +
                        "Thereafter the function parameters I gave you should be used, in that order." +
                        "Go!"
                    )

                    # TODO: Generalize this
                    test_code_to_append_to_implementation = (
                        f"print({run_result.output.function_name}('{self.file_path}'))"
                    )

                    swe_output = await self.swe_runner(deliverable_description, test_code_to_append_to_implementation)

                    logger.info(f"SWE run result: {swe_output}")

                    current_prompt = (
                        "The software engineer agent has submitted a solution.\n" +
                        f"Its result is:\n\n{swe_output}\n\n" +
                        "Choose your action:\n" +
                        "1. Request a function to analyze the data source\n" +
                        "2. If the analysis is sufficient, output the final analysis result\n",
                    )

                    swe_outputs.append(swe_output)

                run_output = run_result.output
                message_history += run_result.new_messages()

            logger.info(
                f"Data source analysis agent run completed, saving results: {run_output.model_dump()}")

            await self._save_results(run_result)

        except Exception as e:
            await patch_run_status(self.project_client, RunStatusUpdate(
                run_id=self.run_id,
                status="failed"
            ))
            logger.error(f"Error running data source analysis agent: {e}")
            raise e

        else:
            return DataSourceAnalysisRunnerOutput(source_analysis=run_output, swe_outputs=swe_outputs)


@broker.task(retry_on_error=False)
async def run_data_source_analysis_task(
        user_id: uuid.UUID,
        source_id: uuid.UUID,
        file_path: str,
        bearer_token: str):

    runner = DataSourceAnalysisRunner(
        user_id,
        source_id,
        file_path,
        bearer_token
    )

    result = await runner()

    return result
