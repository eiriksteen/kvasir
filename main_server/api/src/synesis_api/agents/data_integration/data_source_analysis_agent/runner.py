import uuid
import pandas as pd
from pathlib import Path
from typing import List, Optional
from synesis_api.agents.data_integration.data_source_analysis_agent.agent import data_source_analysis_agent, DataSourceAnalysisAgentDeps, DataSourceAnalysisAgentOutput
from pydantic_ai import Agent
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import FunctionToolCallEvent
from synesis_api.worker import broker, logger
from synesis_api.modules.data_sources.service import fill_tabular_file_data_sources_details
from synesis_api.utils.dataframe_utils import get_df_info


class DataSourceAnalysisRunner:

    def __init__(self, user_id: str, source_ids: List[uuid.UUID], file_paths: List[Path]):
        self.data_source_agent = data_source_analysis_agent
        self.user_id = user_id
        self.source_ids = source_ids
        self.logger = logger
        self.file_paths = file_paths

    async def _run_agent(
            self,
            deps: DataSourceAnalysisAgentDeps,
            user_prompt: Optional[str] = None,
    ) -> AgentRunResult[DataSourceAnalysisAgentOutput]:

        async with self.data_source_agent.iter(
                user_prompt=user_prompt,
                deps=deps) as run:
            async for node in run:
                if Agent.is_call_tools_node(node):
                    async with node.stream(run.ctx) as handle_stream:
                        async for event in handle_stream:
                            if isinstance(event, FunctionToolCallEvent):
                                message = f'[Tools] The LLM calls tool={event.part.tool_name!r} with args={event.part.args}'
                                self.logger.info(message)

        return run.result

    def _create_content_preview(self, file_path: Path) -> str:
        if file_path.suffix == ".csv":
            df = pd.read_csv(file_path)
        elif file_path.suffix == ".json":
            df = pd.read_json(file_path)
        elif file_path.suffix == ".xlsx":
            df = pd.read_excel(file_path)
        elif file_path.suffix == ".parquet":
            df = pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        return get_df_info(df)

    async def _save_results(self, result: DataSourceAnalysisAgentOutput):

        content_previews = [self._create_content_preview(
            file_path) for file_path in self.file_paths]

        await fill_tabular_file_data_sources_details(
            file_record_ids=self.source_ids,
            descriptions=[
                data_source.content_description for data_source in result.data_sources],
            quality_descriptions=[
                data_source.quality_description for data_source in result.data_sources],
            content_previews=content_previews,
            feature_names=[[
                feature.name for feature in data_source.features] for data_source in result.data_sources],
            feature_units=[[
                feature.unit for feature in data_source.features] for data_source in result.data_sources],
            feature_descriptions=[[
                feature.description for feature in data_source.features] for data_source in result.data_sources],
            feature_types=[[
                feature.type for feature in data_source.features] for data_source in result.data_sources],
            feature_subtypes=[[
                feature.subtype for feature in data_source.features] for data_source in result.data_sources],
            feature_scales=[[
                feature.scale for feature in data_source.features] for data_source in result.data_sources],
        )

    async def __call__(self) -> DataSourceAnalysisAgentOutput:

        deps = DataSourceAnalysisAgentDeps(file_paths=self.file_paths)

        result = await self._run_agent(deps)

        await self._save_results(result.output)

        return result


@broker.task(retry_on_error=False)
async def run_data_source_analysis_task(
        user_id: uuid.UUID,
        source_ids: List[uuid.UUID],
        file_paths: List[str]):

    assert len(source_ids) == len(
        file_paths), "The number of source ids must match the number of file paths"

    runner = DataSourceAnalysisRunner(
        user_id, source_ids, [Path(file_path) for file_path in file_paths])
    result = await runner()

    return result
