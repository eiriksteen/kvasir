import pandas as pd
from typing import Literal
from pathlib import Path
from pydantic_ai import Agent, RunContext, ModelRetry, Tool
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
import logging
from synesis_api.modules.ontology.schema import Dataset

class AnalysisPlannerAgent:
    def __init__(
        self
    ):
        self.logger = logging.getLogger(__name__)

        self.provider = OpenAIProvider(api_key=OPENAI_API_KEY)
        self.model = OpenAIModel(
            model_name=OPENAI_API_MODEL,
            provider=self.provider
        )
        self._initialize_agents()
    
    def _initialize_agents(self):
        self.agent = Agent(
            self.model,
            result_type=AnalysisPlan,
            deps_type=AnalysisPlannerDeps,
            name="Analysis Planner Agent",
            model_settings=ModelSettings(temperature=0.1)
            )

        @self.agent.system_prompt
        def get_system_prompt(ctx: RunContext[AnalysisPlannerDeps]) -> str:
            sys_prompt = (
                f"{ANALYSIS_PLANNER_SYSTEM_PROMPT}\n"
                f"The problem description is as follows: {ctx.deps.problem_description}\n"
                f"This is the following datasets: {[dataset.model_dump() for dataset in ctx.deps.datasets]}\n"
                f"The column names for the different datasets are as follows: {ctx.deps.column_names}\n"
                f"Here is a list of tools that you can use in your plan: {ctx.deps.tools}\n. Do not call the tools, just use them in your plan that you present to the user."
            )
            return sys_prompt
    
    
    async def run_analysis_planner(
        self, 
        dfs: List[pd.DataFrame],
        problem_description: str,
        datasets: List[Dataset],
        tools: List[str],
        prompt: str
    ) -> AnalysisPlan:
        deps = AnalysisPlannerDeps(
            datasets=datasets,
            column_names={dataset.id: df.columns.tolist() for dataset, df in zip(datasets, dfs)},
            problem_description=problem_description,
            tools=tools
        )
        nodes = []
        async with self.agent.iter(
            prompt,
            deps=deps
        ) as agent_run:
            async for node in agent_run:
                nodes.append(node)
                self.logger.info(f"Analysis planner agent state: {node}")

        return agent_run.result.data
    
    


class AnalysisExecutionAgent:
    def __init__(
        self,
        tools: List[Tool],
    ):
        self.logger = logging.getLogger(__name__)
        self.tools = tools

        self.provider = OpenAIProvider(api_key=OPENAI_API_KEY)
        self.model = OpenAIModel(
            model_name=OPENAI_API_MODEL,
            provider=self.provider
        )
        self._initialize_agents()

    def _initialize_agents(self):
        self.agent = Agent(
            self.model,
            result_type=AnalysisJobResult,
            deps_type=AnalysisExecutionDeps,
            name="Analysis Execution Agent",
            model_settings=ModelSettings(temperature=0.1),
            tools=self.tools
        )

        @self.agent.system_prompt
        async def get_system_prompt(ctx: RunContext[AnalysisExecutionDeps]) -> str:
            sys_prompt = (
                f"{ANALYSIS_EXECUTION_SYSTEM_PROMPT}\n"
                f"Here is the analysis plan: {ctx.deps.analysis_plan}\n"
                f"If some inputs to the tools are missing or not working here are the column names: {ctx.deps.df.column_names}\n"
            )
            return sys_prompt
        
        @self.agent.tool_plain
        async def execute_python_code(python_code: str):
            """
            Execute a python code block.
            """
            out, err = await run_code_in_container(python_code)

            if err:
                raise ModelRetry(f"Error executing code: {err}")

            return out
    
    async def run_execution_agent(
        self,
        df: pd.DataFrame,
        analysis_plan: AnalysisPlan
    ) -> AnalysisJobResult:
        deps = AnalysisExecutionDeps(
            df=df,
            analysis_plan=analysis_plan
        )
        nodes = []
        async with self.agent.iter(
            "Execute the analysis plan, by calling the tools in the order they are given in the plan.",
            deps=deps
        ) as agent_run:
            async for node in agent_run:
                nodes.append(node)
                self.logger.info(f"Analysis execution agent state: {node}")
        return agent_run.result.data
    
    
    
    