import uuid
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel
from pydantic_ai.agent import AgentRunResult

from project_server.agents.data_source_analysis.agent import data_source_analysis_agent, DataSourceAnalysisAgentDeps
from project_server.agents.data_source_analysis.output import TabularFileAnalysisOutput, CallSWEToImplementFunctionOutput
from project_server.worker import broker
from project_server.agents.swe.runner import SWEAgentRunner
from project_server.agents.data_source_analysis.prompt import DATA_SOURCE_AGENT_SYSTEM_PROMPT
from project_server.agents.swe.output import SWEAgentOutput
from project_server.agents.runner_base import RunnerBase
from project_server.client import (
    post_data_source_analysis,
    post_data_source_details,
)
from synesis_schemas.main_server import (
    TabularFileDataSourceCreate,
    DataSourceAnalysisCreate
)


class DataSourceAnalysisRunnerOutput(BaseModel):
    source_analysis: TabularFileAnalysisOutput
    swe_outputs: List[SWEAgentOutput]


class DataSourceAnalysisRunner(RunnerBase):

    def __init__(self, user_id: str, source_id: uuid.UUID, file_path: str, bearer_token: str, run_id: Optional[uuid.UUID] = None):
        super().__init__(agent=data_source_analysis_agent,
                         user_id=user_id,
                         bearer_token=bearer_token,
                         run_id=run_id,
                         run_type="data_source_analysis")

        self.source_id = source_id
        self.file_path = Path(file_path)
        self.swe_runner = SWEAgentRunner(user_id, bearer_token)

    async def __call__(self) -> DataSourceAnalysisRunnerOutput:

        try:
            await self._create_run_if_not_exists()

            run_output, swe_outputs = None, []

            current_prompt = (
                f"Start analyzing the data source!\n\n" +
                "Choose your action: " +
                "1. Request a function to analyze the data source\n" +
                "2. If the analysis is sufficient, output the final analysis result\n",
            )

            while not isinstance(run_output, TabularFileAnalysisOutput):

                run_result: AgentRunResult = await self._run_agent(
                    current_prompt,
                    output_type=[CallSWEToImplementFunctionOutput,
                                 TabularFileAnalysisOutput],
                    deps=DataSourceAnalysisAgentDeps(file_path=self.file_path),
                )

                if isinstance(run_result.output, CallSWEToImplementFunctionOutput):

                    await self._log_message(f"Calling SWE agent to implement function: {run_result.output}", "result", write_to_db=True)

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
                        f"print(str({run_result.output.function_name}('{self.file_path}'))[:5000])"
                    )

                    swe_output = await self.swe_runner(deliverable_description, test_code_to_append_to_implementation)

                    await self._log_message(f"SWE run result: {swe_output}", "result", write_to_db=True)

                    current_prompt = (
                        "The software engineer agent has submitted a solution.\n" +
                        f"Its result is:\n\n{swe_output}\n\n" +
                        "Choose your action:\n" +
                        "1. Request a function to analyze the data source\n" +
                        "2. If the analysis is sufficient, output the final analysis result\n",
                    )

                    swe_outputs.append(swe_output)

                run_output = run_result.output

            await self._log_message(f"Data source analysis agent run completed, saving results: {run_output.model_dump()}", "result", write_to_db=True)

            await self._save_results(run_result)
            await self._complete_agent_run("Data source analysis agent run completed")

        except Exception as e:
            await self._fail_agent_run(f"Error running data source analysis agent: {e}")
            raise e

        else:
            return DataSourceAnalysisRunnerOutput(source_analysis=run_output, swe_outputs=swe_outputs)

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

        # TODO: Save the SWE functions


@broker.task()
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
