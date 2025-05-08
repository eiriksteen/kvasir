import pandas as pd
from typing import Dict, Tuple
from pathlib import Path
from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.settings import ModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from synesis_api.modules.analysis.agent.tools import eda_cs_basic_tools, eda_cs_advanced_tools
from synesis_api.modules.analysis.agent.prompt import EDA_SYSTEM_PROMPT
from synesis_api.modules.analysis.agent.deps import EDADepsBasic, EDADepsAdvanced, EDADepsIndependent, EDADepsSummary
from synesis_api.secrets import OPENAI_API_KEY, OPENAI_API_MODEL
from synesis_api.modules.analysis.schema import EDAResponse, EDAResponseWithCode
from synesis_api.utils import run_code_in_container, copy_to_container

provider = OpenAIProvider(api_key=OPENAI_API_KEY)

from .tools import eda_cs_basic_tools, eda_cs_advanced_tools #eda_ts_basic_tools, eda_ts_advanced_tools
from .prompt import EDA_SYSTEM_PROMPT, BASIC_PROMPT, ADVANCED_PROMPT, INDEPENDENT_PROMPT, SUMMARIZE_EDA
from .deps import EDADepsBasic, EDADepsAdvanced, EDADepsIndependent, EDADepsTotal
from synesis_api.secrets import OPENAI_API_KEY, OPENAI_API_MODEL
from synesis_api.modules.analysis.schema import AnalysisJobResultMetadata, AnalysisJobResult, AnalysisPlan
from synesis_api.utils import run_code_in_container
from pydantic_ai.messages import SystemPromptPart, ModelRequest
from typing import List
from .prompt import ANALYSIS_AGENT_SYSTEM_PROMPT
from .deps import AnalysisDeps
from synesis_api.secrets import OPENAI_API_KEY, OPENAI_API_MODEL
from synesis_api.modules.analysis.schema import AnalysisJobResult, AnalysisPlan, AnalysisRequest, DelegateResult, AnalysisJobResultMetadataInDB
from synesis_api.utils import run_code_in_container, copy_file_to_container
from synesis_api.modules.ontology.service import get_user_datasets_by_ids
from synesis_api.worker import logger
from pydantic_ai.messages import ModelMessage
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
)
from fastapi import HTTPException
import aiofiles
import uuid
from io import StringIO
from .tools import eda_cs_tools_str
import json
from ...jobs.service import get_job_metadata, update_job_status, create_job
from ..service import (
    get_dataset_ids_by_job_id,
    get_analysis_job_results_from_db,
    get_user_analyses_by_ids,
    insert_analysis_job_results_into_db,
    update_analysis_job_results_in_db
)
from ....auth.service import create_api_key
from datetime import datetime

# Add dataset cache
dataset_cache: Dict[str, pd.DataFrame] = {}

async def load_dataset_from_cache_or_disk(dataset_id: uuid.UUID, user_id: uuid.UUID) -> pd.DataFrame:
    """Load dataset from cache if available, otherwise load from disk and cache it."""
    if dataset_id in dataset_cache:
        logger.info(f"Loading dataset from cache: {dataset_id}")
        return dataset_cache[dataset_id]
    data_path = Path(f"integrated_data/{user_id}/{dataset_id}.csv")
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

# class AnalysisPlannerAgent:
#     def __init__(
#         self
#     ):
#         self.logger = logger

#         self.provider = OpenAIProvider(api_key=OPENAI_API_KEY)
#         self.model = OpenAIModel(
#             model_name=OPENAI_API_MODEL,
#             provider=self.provider
#         )
#         self._initialize_agents()
    
#     def _initialize_agents(self):
#         self.agent = Agent(
#             self.model,
#             result_type=AnalysisPlan,
#             deps_type=AnalysisPlannerDeps,
#             name="Analysis Planner Agent",
#             model_settings=ModelSettings(temperature=0.1)
#             )

#         @self.agent.system_prompt
#         def get_system_prompt(ctx: RunContext[AnalysisPlannerDeps]) -> str:
#             sys_prompt = (
#                 f"{ANALYSIS_PLANNER_SYSTEM_PROMPT}\n"
#                 f"The problem description is as follows: {ctx.deps.problem_description}\n"
#                 f"This is the following datasets: {[dataset.model_dump() for dataset in ctx.deps.datasets]}\n"
#                 f"The column names for the different datasets are as follows: {ctx.deps.column_names}\n"
#                 f"Here is a list of tools that you can use in your plan: {ctx.deps.tools}\n. Do not call the tools, just use them in your plan that you present to the user."
#             )
#             return sys_prompt
    
    


class AnalysisExecutionAgent:
    def __init__(
        self,
        # tools: List[Tool],
    ):
        self.logger = logger
        # self.tools = tools

        self.provider = OpenAIProvider(api_key=OPENAI_API_KEY)
        self.model = OpenAIModel(
            model_name=OPENAI_API_MODEL,
            provider=self.provider
        )
        self._initialize_agents()

    def _initialize_agents(self):
        self.agent = Agent(
            self.model,
            system_prompt=ANALYSIS_AGENT_SYSTEM_PROMPT,
            deps_type=AnalysisDeps,
            name="Analysis Execution Agent",
            model_settings=ModelSettings(temperature=0.1),
        )

        # @self.agent.system_prompt
        # async def get_system_prompt(ctx: RunContext[AnalysisExecutionDeps]) -> str:
        #     _, err = await copy_file_to_container(ctx.deps.data_path, target_dir="/tmp")

        #     if err:
        #         raise ValueError(f"Error copying file to container: {err}")

        #     sys_prompt = (
        #         f"{ANALYSIS_AGENT_SYSTEM_PROMPT}\n"
        #         f"Here is the analysis plan: {ctx.deps.analysis_plan}\n"
        #         f"If some inputs to the tools are missing or not working here are the column names: {ctx.deps.df.columns}\n"
        #         f"If you crete code yourself, you can retrieve the data from the following path: /tmp/{ctx.deps.data_path.name}\n"
        #     )
        #     return sys_prompt
        
        @self.agent.tool_plain()
        async def execute_python_code(python_code: str):
            """
            Execute a python code block.
            """
            out, err = await run_code_in_container(python_code)
            if err:
                # Instead of retrying, return the error message
                return f"Error executing code: {err}\n\nPlease fix the code and try again."

            return out
        

    async def delegate(self, prompt: str):
        prompt = "This is the user prompt: " + prompt + "You can delegate the task to one of the following functions: " + ", ".join([f"'{func}'" for func in ["run_analysis_planner", "run_execution_agent", "run_simple_analysis"]]) + ". Which function do you want to delegate the task to?"

        result = await self.agent.run(
            prompt, 
            output_type=DelegateResult
        )
        return result.output.function_name

    async def run_analysis_planner(
        self,
        analysis_request: AnalysisRequest,
    ):
        analysis_deps, message_history = await self._prepare_agent_run(analysis_request, "analysis_planner")

        if len(analysis_request.analysis_ids) == 0:
            try: 
                self.logger.info("Creating analysis job")
                api_key = await create_api_key(analysis_request.user)
                analysis_job = await create_job(analysis_request.user.id, api_key.id, "analysis")
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail="Failed to create analysis job.")
        else:
            analysis_job = await get_job_metadata(analysis_request.analysis_ids[0])

        nodes = []
        async with self.agent.iter(
            analysis_request.prompt,
            output_type=AnalysisPlan,
            message_history=message_history,
            deps=analysis_deps
        ) as agent_run:
            async for node in agent_run:
                nodes.append(node)
                self.logger.info(f"Analysis planner agent state: {node}")

        
        result = AnalysisJobResultMetadataInDB(
            job_id=analysis_job.id,
            number_of_datasets=len(analysis_request.dataset_ids),
            number_of_automations=len(analysis_request.automation_ids),
            dataset_ids=analysis_request.dataset_ids,
            automation_ids=analysis_request.automation_ids,
            analysis_plan=agent_run.result.output,
            created_at=datetime.now(),
            pdf_created=False,
            user_id=analysis_request.user.id,
        )

        if len(analysis_request.analysis_ids) == 0:
            await insert_analysis_job_results_into_db(result)
        else:
            await update_analysis_job_results_in_db(result)


    async def run_analysis_execution(
        self,
        analysis_request: AnalysisRequest,
    ) -> AnalysisJobResult:
        analysis_deps, message_history = await self._prepare_agent_run(analysis_request, "analysis_execution")
        nodes = []
        async with self.agent.iter(
            "Execute the analysis plan, by calling the tools in the order they are given in the plan.",
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
        
        logger.info(f"analysis_request.analysis_ids: {analysis_request.analysis_ids}")
        logger.info(f"type: {analysis_type}")
        if len(analysis_request.analysis_ids) > 0 and analysis_type == "analysis_planner":
            analyses = await get_user_analyses_by_ids(analysis_request.user.id, analysis_request.analysis_ids)
            logger.info(f"analyses: {analyses}")

            for dataset_id in analyses.analysis_job_results[0].dataset_ids:
                if dataset_id not in analysis_request.dataset_ids:
                    analysis_request.dataset_ids.append(dataset_id)

            for automation_id in analyses.analysis_job_results[0].automation_ids:
                if automation_id not in analysis_request.automation_ids:
                    analysis_request.automation_ids.append(automation_id)

            for analysis in analyses.analysis_job_results:
                await update_job_status(analysis.job_id, "running") # TODO: this should only be done when the analysis is actually running, what if the analysis in context should not be changed?


        try: 
            datasets = await get_user_datasets_by_ids(analysis_request.user.id, analysis_request.dataset_ids)
        except:
            raise HTTPException(
                status_code=500, detail="Failed to get datasets.")
        
        data_dir = Path("integrated_data") / f"{analysis_request.user.id}"
        data_paths = [data_dir / f"{dataset_id}.csv" for dataset_id in analysis_request.dataset_ids]
        problem_description = ""

        dfs = [] # we should store column names in the dataset object
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
                content= f"""
                    {ANALYSIS_AGENT_SYSTEM_PROMPT}\n
                    Here are the column names: {analysis_deps.df.columns.tolist()}\n
                    Here are some functions you can use to plan an analysis: {eda_cs_tools_str}\n
                    If you create code yourself, you can retrieve the data from the following path: /tmp/{data_paths[0].name}\n 
                    Here is the problem description: {problem_description}\n
                    Here are the analysis plans: {analyses.model_dump_json()}\n
                    Remember to not actually call the functions, just list them in your plan. The plan will be executed later.
                """
            )
        else:
            system_prompt = SystemPromptPart(
                content= f"""
                    {ANALYSIS_AGENT_SYSTEM_PROMPT}\n
                    Here are the column names: {analysis_deps.df.columns.tolist()}\n
                    If you create code yourself, you can retrieve the data from the following path: /tmp/{data_paths[0].name}\n 
                """
                    # Here are some functions you can use to execute an analysis: {eda_cs_tools_str}\n
            )
        model_request = ModelRequest(parts=[system_prompt])
        message_history = analysis_request.message_history + [model_request]
        print(f"message_history: {message_history}")

        return analysis_deps, message_history
        
        
# analysis_planner_agent = AnalysisPlannerAgent()
analysis_agent = AnalysisExecutionAgent()