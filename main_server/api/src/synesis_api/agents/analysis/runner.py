import pandas as pd
from pathlib import Path
from pydantic_ai import Agent
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import SystemPromptPart, ModelRequest
from typing import Dict, Tuple, List, Literal
from synesis_api.agents.analysis.prompt import ANALYSIS_AGENT_SYSTEM_PROMPT
from synesis_api.agents.analysis.agent import analysis_agent, AnalysisDeps
from synesis_api.modules.analysis.schema import AnalysisJobResult, AnalysisJobResultMetadataInDB, AnalysisPlan
from synesis_api.modules.data_objects_old.service.metadata_service import get_user_datasets_by_ids
from synesis_api.worker import logger, broker
from pydantic_ai.messages import (
    ModelMessage,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
)
from fastapi import HTTPException
import aiofiles
import uuid
from io import StringIO
from synesis_api.modules.runs.service import get_runs, update_run_status, create_run, create_run_message_pydantic
from synesis_api.modules.analysis.service import (
    get_user_analyses_by_ids,
    insert_analysis_job_results_into_db,
    update_analysis_job_results_in_db
)
from datetime import datetime
from synesis_api.redis import get_redis
from synesis_api.base_schema import BaseSchema
from synesis_api.auth.schema import User
from uuid import UUID
from synesis_api.modules.project.service import add_entity_to_project
# from synesis_api.modules.project.schema import ProjectUpdate
from synesis_api.modules.node.router import create_node
from synesis_api.modules.node.schema import FrontendNodeCreate

# Add dataset cache
dataset_cache: Dict[str, pd.DataFrame] = {}


async def load_dataset_from_cache_or_disk(dataset_id: uuid.UUID, user_id: uuid.UUID) -> pd.DataFrame:
    """Load dataset from cache if available, otherwise load from disk and cache it."""
    if dataset_id in dataset_cache:
        logger.info(f"Loading dataset from cache: {dataset_id}")
        return dataset_cache[dataset_id]
    logger.info(f"Loading dataset from disk: {dataset_id}")
    import os
    logger.info(f"Current working directory: {os.getcwd()}")
    data_path = Path(f"integrated_data/{user_id}/{dataset_id}/dataset.csv")
    try:
        async with aiofiles.open(data_path, 'r', encoding="utf-8") as f:
            content = await f.read()
            df = pd.read_csv(StringIO(content))
            dataset_cache[data_path] = df
            logger.info(f"Cached dataset: {data_path}")
            return df
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"File in {data_path} not found: {str(e)}"
        )


class AnalysisRequest(BaseSchema):
    project_id: UUID
    dataset_ids: List[UUID] = []
    analysis_ids: List[UUID] = []
    automation_ids: List[UUID] = []
    prompt: str | None = None
    user: User
    message_history: List[ModelMessage] = []
    conversation_id: UUID


class DelegateResult(BaseSchema):
    function_name: Literal["run_analysis_planner",
                           "run_execution_agent",
                           "run_simple_analysis"]


class AnalysisAgentRunner:
    def __init__(
        self
    ):
        self.logger = logger
        self.redis_stream = get_redis()
        self.agent = analysis_agent

    async def post_message_to_redis(self, message: dict, job_id: uuid.UUID):
        message = {
            "id": str(message["id"]),
            "job_id": str(message["job_id"]),
            "type": message["type"],
            "message": message["message"],
            "created_at": message["created_at"].isoformat()
        }
        await self.redis_stream.xadd(str(job_id), message)

    async def run_analysis_planner(
        self,
        analysis_request: AnalysisRequest,
    ):

        analysis_deps, message_history = await self._prepare_agent_run(analysis_request, "analysis_planner")
        status_messages = []
        job_id = uuid.uuid4()

        if len(analysis_request.analysis_ids) == 0:
            try:
                self.logger.info("Creating analysis job")
                # api_key = await create_api_key(analysis_request.user)
                job_name = await self.agent.run(
                    f"The user prompt is: {analysis_request.prompt}. The user prompt is about to be performed, but the user has not given a name to the analysis job. Give a short name to the analysis job that is about to be performed. Do not make an analysis yet. Only give a name.",
                    message_history=message_history,
                    output_type=str
                )
                job_name = job_name.output.replace(
                    '"', '').replace("'", "").strip()
                analysis_job = await create_run(analysis_request.user.id, "analysis", job_id, job_name)
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to create analysis job: {str(e)}")
        else:
            analysis_job = await get_runs(analysis_request.user.id, analysis_request.analysis_ids[0])

        status_message = {
            "id": uuid.uuid4(),
            "job_id": analysis_job.id,
            "type": "tool_call",
            "message": "Loading datasets...",
            "created_at": datetime.now()
        }
        status_messages.append(status_message)
        await self.post_message_to_redis(status_message, analysis_job.id)

        nodes = []

        status_message = {
            "id": uuid.uuid4(),
            "job_id": analysis_job.id,
            "type": "tool_call",
            "message": "Starting analysis planner...",
            "created_at": datetime.now()
        }
        status_messages.append(status_message)
        await self.post_message_to_redis(status_message, analysis_job.id)

        async with self.agent.iter(
            analysis_request.prompt,
            output_type=AnalysisPlan,
            message_history=message_history,
            deps=analysis_deps
        ) as agent_run:
            async for node in agent_run:
                nodes.append(node)
                self.logger.info(f"Analysis planner agent state: {node}")

                if Agent.is_call_tools_node(node):
                    async with node.stream(agent_run.ctx) as handle_stream:
                        async for event in handle_stream:
                            if isinstance(event, FunctionToolCallEvent):
                                status_message = {
                                    "id": uuid.uuid4(),
                                    "job_id": analysis_job.id,
                                    "type": "tool_call",
                                    "message": f"Calling {event.part.tool_name}...",
                                    "created_at": datetime.now()
                                }
                                status_messages.append(status_message)
                                await self.post_message_to_redis(status_message, analysis_job.id)

                elif Agent.is_user_prompt_node(node):
                    status_message = {
                        "id": uuid.uuid4(),
                        "job_id": analysis_job.id,
                        "type": "user_prompt",
                        "message": str(node.user_prompt),
                        "created_at": datetime.now()
                    }
                    status_messages.append(status_message)
                    await self.post_message_to_redis(status_message, analysis_job.id)

                elif Agent.is_end_node(node):
                    status_message = {
                        "id": uuid.uuid4(),
                        "job_id": analysis_job.id,
                        "type": "analysis_result",
                        "message": str(node),
                        "created_at": datetime.now()
                    }
                    status_messages.append(status_message)
                    await self.post_message_to_redis(status_message, analysis_job.id)

        result = AnalysisJobResultMetadataInDB(
            job_id=analysis_job.id,
            name=job_name,
            number_of_datasets=len(analysis_request.dataset_ids),
            number_of_automations=len(analysis_request.automation_ids),
            dataset_ids=analysis_request.dataset_ids,
            automation_ids=analysis_request.automation_ids,
            analysis_plan=agent_run.result.output,
            created_at=datetime.now(),
            pdf_created=False,
            user_id=analysis_request.user.id,
            status_messages=status_messages
        )

        if len(analysis_request.analysis_ids) == 0:
            await insert_analysis_job_results_into_db(result)
            await add_entity_to_project(analysis_request.project_id, "analysis", analysis_job.id)

            frontend_node = FrontendNodeCreate(
                project_id=analysis_request.project_id,
                x_position=300.0,
                y_position=0.0,
                type="analysis",
                dataset_id=None,
                analysis_id=analysis_job.id,
                automation_id=None,
            )
            await create_node(frontend_node)

        else:
            await update_analysis_job_results_in_db(result)

    async def run_analysis_execution(
        self,
        analysis_request: AnalysisRequest,
    ) -> AnalysisJobResult:
        analysis_deps, message_history = await self._prepare_agent_run(analysis_request, "analysis_execution")
        nodes = []
        async with self.agent.iter(
            "Execute the analysis. If you have been given a plan, execute the analysis plan by calling the tools in the order they are given in the plan.",
            deps=analysis_deps,
            message_history=message_history
        ) as agent_run:
            async for node in agent_run:
                nodes.append(node)
                self.logger.info(f"Analysis execution agent state: {node}")
        return agent_run.result

    async def run_simple_analysis(
        self,
        analysis_request: AnalysisRequest,
    ):
        analysis_deps, message_history = await self._prepare_agent_run(analysis_request, "simple_analysis")

        async with self.agent.iter(
            analysis_request.prompt,
            output_type=AnalysisJobResult,
            message_history=message_history,
            deps=analysis_deps
        ) as run:
            async for node in run:
                if Agent.is_call_tools_node(node):
                    async with node.stream(run.ctx) as handle_stream:
                        async for event in handle_stream:
                            if isinstance(event, FunctionToolCallEvent):
                                if event.part.tool_name == "execute_python_code":
                                    yield f"Executing python code..."
                                else:
                                    yield f"Calling cached tool for analysis..."
                                    print(event)
                            elif isinstance(event, FunctionToolResultEvent):
                                yield "Tool results available..."
                elif Agent.is_end_node(node):
                    yield "Formatting result..."
        yield run.result

    async def _prepare_agent_run(self, analysis_request: AnalysisRequest, analysis_type=str) -> Tuple[AnalysisDeps, List[ModelMessage]]:
        if analysis_type == "simple_analysis":
            if len(analysis_request.dataset_ids) == 0 and len(analysis_request.automation_ids) == 0:
                raise HTTPException(
                    status_code=400, detail="At least one dataset or automation is required.")

        logger.info(
            f"analysis_request.analysis_ids: {analysis_request.analysis_ids}")
        logger.info(f"type: {analysis_type}")
        if len(analysis_request.analysis_ids) > 0 and analysis_type == "analysis_planner":
            analyses = await get_user_analyses_by_ids(analysis_request.user.id, analysis_request.analysis_ids)
            logger.info(f"analyses: {analyses}")

            for dataset_id in analyses.analyses_job_results[0].dataset_ids:
                if dataset_id not in analysis_request.dataset_ids:
                    analysis_request.dataset_ids.append(dataset_id)

            for automation_id in analyses.analyses_job_results[0].automation_ids:
                if automation_id not in analysis_request.automation_ids:
                    analysis_request.automation_ids.append(automation_id)

            for analysis in analyses.analyses_job_results:
                # TODO: this should only be done when the analysis is actually running, what if the analysis in context should not be changed?
                await update_run_status(analysis.job_id, "running")

        try:
            datasets = await get_user_datasets_by_ids(analysis_request.user.id, analysis_request.dataset_ids)
        except:
            raise HTTPException(
                status_code=500, detail="Failed to get datasets.")

        data_dir = Path("integrated_data") / f"{analysis_request.user.id}"
        data_paths = [
            data_dir / f"{dataset_id}.csv" for dataset_id in analysis_request.dataset_ids]
        problem_description = ""

        dfs = []  # we should store column names in the dataset object
        try:
            logger.info(f"Start loading datasets")
            for dataset in datasets.time_series:
                df = await load_dataset_from_cache_or_disk(dataset.id, dataset.user_id)
                dfs.append(df)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error loading datasets: {str(e)}"
            )

        analysis_deps = AnalysisDeps(
            df=dfs[0],  # TODO: handle multiple datasets
        )

        # TODO: add more to this system prompt when you make functionality for multiple datasets
        if len(analysis_request.analysis_ids) > 0 and analysis_type == "analysis_planner":
            system_prompt = SystemPromptPart(
                content=f"""
                    {ANALYSIS_AGENT_SYSTEM_PROMPT}\n
                    Here are the column names: {analysis_deps.df.columns.tolist()}\n
                    Here is the problem description: {problem_description}\n
                    If you create code yourself, you can retrieve the data from the following path: /tmp/6535611e-4a8d-45a8-944b-ea71420616da/DailyDelhiClimateTrain.csv\n 
                    Here are the analysis plans: {analyses.model_dump_json()}\n
                    Remember to not actually call the functions, just list them in your plan. The plan will be executed later.
                """
                # If you create code yourself, you can retrieve the data from the following path: /tmp/{data_paths[0].name}\n  #TODO: THE DATA IS SAVED IN A STUPID WAY NOW
                # Here are some functions you can use to plan an analysis: {eda_cs_tools_str}\n
            )
        else:
            system_prompt = SystemPromptPart(
                content=f"""
                    {ANALYSIS_AGENT_SYSTEM_PROMPT}\n
                    Here are the column names: {analysis_deps.df.columns.tolist()}\n
                    If you create code yourself, you can retrieve the data from the following path: /tmp/6535611e-4a8d-45a8-944b-ea71420616da/DailyDelhiClimateTrain.csv\n 
                """
                # Here are some functions you can use to execute an analysis: {eda_cs_tools_str}\n
            )
        model_request = ModelRequest(parts=[system_prompt])
        message_history = analysis_request.message_history + [model_request]

        return analysis_deps, message_history

    async def __call__(self, analysis_request: AnalysisRequest, analysis_type: Literal["run_analysis_planner", "run_execution_agent"]):
        await create_run_message_pydantic(analysis_request.conversation_id, text)

        if analysis_type == "run_analysis_planner":
            text = "Running analysis planner. This may take a couple of minutes. The results will be shown in the analysis tab."
            yield text
            await self.run_analysis_planner(analysis_request)
        elif analysis_type == "run_execution_agent":
            text = "Running analysis execution. This may take a couple of minutes. The results will be shown in the analysis tab."
            yield text
            await self.run_analysis_execution(analysis_request)


@broker.task
async def run_analysis_task(
    project_id: uuid.UUID,
    dataset_ids: List[uuid.UUID],
    automation_ids: List[uuid.UUID],
    analysis_ids: List[uuid.UUID],
    prompt: str,
    context_message: str,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID
) -> AnalysisJobResultMetadataInDB:

    delegation_prompt = (f"This is the current context: {context_message}. "
                         f"This is the user prompt: {prompt}. "
                         "You can delegate the task to one of the following functions: "
                         "[run_analysis_planner, run_execution_agent, run_simple_analysis]. "
                         "Which function do you want to delegate the task to?")
    delegated_task = await analysis_agent.run(delegation_prompt, output_type=DelegateResult)
    delegated_task = delegated_task.output.function_name

    analysis_request = AnalysisRequest(
        project_id=project_id,
        dataset_ids=dataset_ids,
        automation_ids=automation_ids,
        analysis_ids=analysis_ids,
        prompt=prompt,
        user_id=user_id,
        conversation_id=conversation_id
    )

    runner = AnalysisAgentRunner()

    await runner(analysis_request, delegated_task)


# @broker.task
# async def run_analysis_task(
#     analysis_request: AnalysisRequest,
#     analysis_type: Literal["run_analysis_planner", "run_execution_agent"]
# ) -> AnalysisJobResultMetadataInDB:
#     runner = AnalysisAgentRunner()
#     await runner(analysis_request, analysis_type)
