import pandas as pd
from typing import Literal
from pathlib import Path
from pydantic_ai import Agent, RunContext, ModelRetry
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
from ....secrets import OPENAI_API_KEY, OPENAI_API_MODEL
from ..schema import EDAResponse, EDAResponseWithCode, EDAResponseSummary, EDAResponseTotal
from ....utils import run_code_in_container, copy_file_to_container
from celery.utils.log import get_task_logger


class EDAAgent:
    def __init__(
        self,
        df: pd.DataFrame,
        data_type: Literal["time_series", "tabular", "image", "text"],
        data_description: str,
        problem_description: str,
        data_path: Path
    ):
        if data_type not in ["time_series", "tabular", "image", "text"]:
            raise ValueError(f"Unsupported data type: {data_type}")
        self.celery_logger = get_task_logger(__name__)
        self.df = df
        self.data_type = data_type
        self.data_description = data_description
        self.problem_description = problem_description
        self.data_path = data_path

        if self.data_type == "tabular" or self.data_type == "time_series":
            self.basic_tools = eda_cs_basic_tools
            self.advanced_tools = eda_cs_advanced_tools
        # elif self.data_type == "time_series":
        #     self.basic_tools = eda_ts_basic_tools
        #     self.advanced_tools = eda_ts_advanced_tools

        self.provider = OpenAIProvider(api_key=OPENAI_API_KEY)
        self.model = OpenAIModel(
            model_name=OPENAI_API_MODEL,
            provider=self.provider
        )
        self._initialize_agents()
    
    def _initialize_agents(self):
        if self.data_type == "time_series" or self.data_type == "tabular":
            self._initialize_ts_tabular_agents()
        else:
            raise ValueError(f"Unsupported data type: {self.data_type}")
    
    def _initialize_ts_tabular_agents(self):
        self.basic_agent = Agent(
            self.model,
            result_type=EDAResponse,
            deps_type=EDADepsBasic,
            name="Basic EDA Agent",
            model_settings=ModelSettings(temperature=0.1),
            tools=self.basic_tools,
        )
        self.advanced_agent = Agent(
            self.model,
            result_type=EDAResponse,
            deps_type=EDADepsAdvanced,
            name="Advanced EDA Agent",
            model_settings=ModelSettings(temperature=0.1),
            tools=self.advanced_tools,
        )
        self.independent_agent = Agent(
            self.model,
            result_type=EDAResponseWithCode,
            deps_type=EDADepsIndependent,
            name="Independent EDA Agent",
            model_settings=ModelSettings(temperature=0.1),
        )

        @self.basic_agent.system_prompt
        def get_system_prompt(ctx: RunContext[EDADepsBasic]) -> str:
            sys_prompt = (
                f"{EDA_SYSTEM_PROMPT}\n"
                f"The problem description is as follows: {ctx.deps.problem_description}\n"
                f"The data description is as follows: {ctx.deps.data_description}\n"
                f"The column names are as follows: {ctx.deps.column_names}\n"
            )
            return sys_prompt

        @self.advanced_agent.system_prompt
        def get_system_prompt(ctx: RunContext[EDADepsAdvanced]) -> str:
            sys_prompt = (
                f"{EDA_SYSTEM_PROMPT}\n"
                f"The problem description is as follows: {ctx.deps.problem_description}\n"
                f"The data description is as follows: {ctx.deps.data_description}\n"
                f"The column names are as follows: {ctx.deps.column_names}\n"
                f"The result from the basic data analysis: {ctx.deps.basic_eda}"
            )
            return sys_prompt


        @self.independent_agent.system_prompt
        async def get_system_prompt(ctx: RunContext[EDADepsIndependent]) -> str:
            _, err = await copy_file_to_container(ctx.deps.data_path, target_dir="/tmp")

            if err:
                raise ValueError(f"Error copying file to container: {err}")

            sys_prompt = (
                f"{EDA_SYSTEM_PROMPT}\n"
                f"The problem description is as follows: {ctx.deps.problem_description}\n"
                f"The data description is as follows: {ctx.deps.data_description}\n"
                f"The column names are as follows: {ctx.deps.column_names}\n"
                f"The result from the basic data analysis: {ctx.deps.basic_eda}\n"
                f"The result from the advanced data analysis: {ctx.deps.advanced_eda}\n"
                f"The path to load the dataframe: /tmp/{ctx.deps.data_path.name}"
            )
            return sys_prompt


        @self.independent_agent.tool_plain
        async def execute_python_code(python_code: str):
            """
            Execute a python code block.
            """
            out, err = await run_code_in_container(python_code)

            if err:
                raise ModelRetry(f"Error executing code: {err}")

            return out

    
    async def run_basic_analysis(self) -> EDAResponse:
        deps = EDADepsBasic(
            data_description=self.data_description,
            column_names=', '.join(self.df.columns.tolist()),
            data_type=self.data_type,
            problem_description=self.problem_description,
            api_key=None,
            df=self.df,
        )
        nodes = []
        async with self.basic_agent.iter(
            BASIC_PROMPT,
            deps=deps
        ) as agent_run:
            async for node in agent_run:
                nodes.append(node)
                self.celery_logger.info(f"Integration agent state: {node}")

        return agent_run.result.data
    
    async def run_advanced_analysis(self, basic_analysis: EDAResponse) -> EDAResponse:
        deps = EDADepsAdvanced(
            data_description=self.data_description,
            column_names=', '.join(self.df.columns.tolist()),
            data_type=self.data_type,
            problem_description=self.problem_description,
            api_key=None,
            df=self.df,
            basic_eda=basic_analysis.analysis
        )
        nodes = []
        async with self.advanced_agent.iter(
            ADVANCED_PROMPT,
            deps=deps
        ) as agent_run:
            async for node in agent_run:
                nodes.append(node)
                self.celery_logger.info(f"Integration agent state: {node}")

        return agent_run.result.data
    
    async def run_independent_analysis(
        self,
        basic_analysis: EDAResponse,
        advanced_analysis: EDAResponse
    ) -> EDAResponseWithCode:
        deps = EDADepsIndependent(
            data_description=self.data_description,
            column_names=', '.join(self.df.columns.tolist()),
            data_type=self.data_type,
            problem_description=self.problem_description,
            api_key=None,
            basic_eda=basic_analysis.analysis,
            advanced_eda=advanced_analysis.analysis,
            data_path=self.data_path,
        )
        nodes = []
        async with self.independent_agent.iter(
            INDEPENDENT_PROMPT,
            deps=deps
        ) as agent_run:
            async for node in agent_run:
                nodes.append(node)
                self.celery_logger.info(f"Integration agent state: {node}")
        return agent_run.result.data
    
    
    
    async def run_full_analysis(self) -> EDAResponseTotal:
        if self.data_type == "time_series" or self.data_type == "tabular":
            self.celery_logger.info("Running basic analysis")
            # basic = await self.run_basic_analysis()
            basic = EDAResponse(analysis="No finds from basic")
            self.celery_logger.info("Basic analysis completed")
            self.celery_logger.info("Running advanced analysis")
            # advanced = await self.run_advanced_analysis(basic)
            advanced = EDAResponse(analysis="No finds from advanced")
            self.celery_logger.info("Advanced analysis completed")
            self.celery_logger.info("Running independent analysis")
            # independent = await self.run_independent_analysis(basic, advanced)
            independent = EDAResponseWithCode(analysis="Another update", python_code="No code from independent")
            self.celery_logger.info("Independent analysis completed")
            self.celery_logger.info(independent.python_code)
            return EDAResponseTotal(
                basic_eda=basic.analysis,
                advanced_eda=advanced.analysis,
                independent_eda=independent.analysis,
                python_code=independent.python_code
            )



    
class SummaryEDAAgent:
    def __init__(
        self,
        df: pd.DataFrame,
        data_type: Literal["time_series", "tabular", "image", "text"],
        data_description: str,
        problem_description: str,
        data_path: Path,
        basic_analysis: str,
        advanced_analysis: str,
        independent_analysis: str,
        independent_analysis_code: str
    ):
        if data_type not in ["time_series", "tabular", "image", "text"]:
            raise ValueError(f"Unsupported data type: {data_type}")
        self.celery_logger = get_task_logger(__name__)
        self.df = df
        self.data_type = data_type
        self.data_description = data_description
        self.problem_description = problem_description
        self.data_path = data_path
        self.basic_analysis = basic_analysis
        self.advanced_analysis = advanced_analysis
        self.independent_analysis = independent_analysis
        self.independent_analysis_code = independent_analysis_code

        self.provider = OpenAIProvider(api_key=OPENAI_API_KEY)
        self.model = OpenAIModel(
            model_name=OPENAI_API_MODEL,
            provider=self.provider
        )
        self._initialize_agents()

    def _initialize_agents(self):
        self.summary_agent = Agent(
            self.model,
            result_type=EDAResponseSummary,
            deps_type=EDADepsTotal,
            name="Summary EDA Agent",
            model_settings=ModelSettings(temperature=0.1),
        )
        @self.summary_agent.system_prompt
        async def get_system_prompt(ctx: RunContext[EDADepsTotal]) -> str:
            sys_prompt = (
                f"{EDA_SYSTEM_PROMPT}\n"
                f"The problem description is as follows: {ctx.deps.problem_description}\n"
                f"The data description is as follows: {ctx.deps.data_description}\n"
                f"The result from the basic data analysis: {ctx.deps.basic_eda}\n"
                f"The result from the advanced data analysis: {ctx.deps.advanced_eda}\n"
                f"The result from the independent data anlysis: {ctx.deps.independent_eda}\n"
                f"The code used in the independent data analysis: {ctx.deps.python_code}"
            )
            return sys_prompt

    async def run_summary_analysis(
        self
    ) -> EDAResponseWithCode:
        deps = EDADepsTotal(
            data_description=self.data_description,
            column_names=', '.join(self.df.columns.tolist()),
            data_type=self.data_type,
            problem_description=self.problem_description,
            api_key=None,
            basic_eda=self.basic_analysis.analysis,
            advanced_eda=self.advanced_analysis.analysis,
            independent_eda=self.independent_analysis.analysis,
            python_code=self.independent_analysis.python_code
        )
        response = await self.summary_agent.run(user_prompt=SUMMARIZE_EDA, deps=deps)
        return response.data
    
    