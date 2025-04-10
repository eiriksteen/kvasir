from typing import Literal, Optional
import pandas as pd
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
from .deps import EDADepsBasic, EDADepsAdvanced, EDADepsIndependent, EDADepsSummary
from ....secrets import OPENAI_API_KEY, OPENAI_API_MODEL
from ..schema import EDAResponse, EDAResponseWithCode
from ....utils import run_code_in_container, copy_file_to_container
from celery.utils.log import get_task_logger


class EDAAgent:
    def __init__(
        self,
        df: pd.DataFrame,
        data_type: Literal["time_series", "tabular", "image", "text"],
        data_description: str,
        problem_description: str,
        data_path: Optional[str] = None
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
            system_prompt=EDA_SYSTEM_PROMPT,
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
        self.summary_agent = Agent(
            self.model,
            result_type=EDAResponseWithCode,
            deps_type=EDADepsSummary,
            name="Summary EDA Agent",
            model_settings=ModelSettings(temperature=0.1),
        )

        @self.advanced_agent.system_prompt
        def get_system_prompt(ctx: RunContext[EDADepsAdvanced]) -> str:
            sys_prompt = (
                f"{EDA_SYSTEM_PROMPT}\n"
                f"The problem description is as follows: {ctx.deps.problem_description}\n"
                f"The data description is as follows: {ctx.deps.data_description}\n"
                f"The result from the basic data analysis: {ctx.deps.basic_data_analysis}"
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
                f"The result from the basic data analysis: {ctx.deps.basic_data_analysis}\n"
                f"The result from the advanced data analysis: {ctx.deps.advanced_data_analysis}\n"
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


        @self.summary_agent.system_prompt
        async def get_system_prompt(ctx: RunContext[EDADepsSummary]) -> str:
            sys_prompt = (
                f"{EDA_SYSTEM_PROMPT}\n"
                f"The problem description is as follows: {ctx.deps.problem_description}\n"
                f"The data description is as follows: {ctx.deps.data_description}\n"
                f"The result from the basic data analysis: {ctx.deps.basic_data_analysis}\n"
                f"The result from the advanced data analysis: {ctx.deps.advanced_data_analysis}\n"
                f"The result from the independent data anlysis: {ctx.deps.independent_data_analysis}\n"
                f"The code used in the independent data analysis: {ctx.deps.python_code}"
            )
            return sys_prompt

    
    
    async def run_basic_analysis(self) -> EDAResponse:
        deps = EDADepsBasic(
            data_description=self.data_description,
            data_type=self.data_type,
            problem_description=self.problem_description,
            api_key=None,
            df=self.df,
        )
        response = await self.basic_agent.run(user_prompt=BASIC_PROMPT, deps=deps)
        return response.data
    
    async def run_advanced_analysis(self, basic_analysis: EDAResponse) -> EDAResponse:
        self.celery_logger.info("we get here")
        deps = EDADepsAdvanced(
            data_description=self.data_description,
            data_type=self.data_type,
            problem_description=self.problem_description,
            api_key=None,
            df=self.df,
            basic_data_analysis=basic_analysis.detailed_summary
        )
        self.celery_logger.info("we get here 2")
        response = await self.advanced_agent.run(user_prompt=ADVANCED_PROMPT, deps=deps)
        return response.data
    
    async def run_independent_analysis(
        self,
        basic_analysis: EDAResponse,
        advanced_analysis: EDAResponse
    ) -> EDAResponseWithCode:
            
        deps = EDADepsIndependent(
            data_description=self.data_description,
            data_type=self.data_type,
            problem_description=self.problem_description,
            api_key=None,
            basic_data_analysis=basic_analysis.detailed_summary,
            advanced_data_analysis=advanced_analysis.detailed_summary,
            data_path=self.data_path,
        )
        response = await self.independent_agent.run(user_prompt=INDEPENDENT_PROMPT, deps=deps)
        return response.data
    
    async def run_summary_analysis(
        self,
        basic_analysis: EDAResponse,
        advanced_analysis: EDAResponse,
        independent_analysis: EDAResponseWithCode
    ) -> EDAResponseWithCode:
        deps = EDADepsSummary(
            data_description=self.data_description,
            data_type=self.data_type,
            problem_description=self.problem_description,
            api_key=None,
            basic_data_analysis=basic_analysis.detailed_summary,
            advanced_data_analysis=advanced_analysis.detailed_summary,
            independent_data_analysis=independent_analysis.detailed_summary,
            python_code=independent_analysis.python_code
        )
        response = await self.summary_agent.run(user_prompt=SUMMARIZE_EDA, deps=deps)
        return response.data
    
    async def run_full_analysis(self) -> EDAResponseWithCode:
        if self.data_type == "time_series" or self.data_type == "tabular":
            self.celery_logger.info("Running basic analysis")
            # basic = await self.run_basic_analysis()
            basic = EDAResponse(detailed_summary="No finds from basic")
            self.celery_logger.info("Basic analysis completed")
            self.celery_logger.info("Running advanced analysis")
            advanced = await self.run_advanced_analysis(basic)
            self.celery_logger.info("Advanced analysis completed")
            self.celery_logger.info("Running independent analysis")
            # TODO: MUST KNOW ABOUT COLUMN NAMES BEFORE DOING ANALYSIS
            independent = await self.run_independent_analysis(basic, advanced)
            self.celery_logger.info("Independent analysis completed")
            self.celery_logger.info("Running summary analysis")
            summary = await self.run_summary_analysis(basic, advanced, independent)
            self.celery_logger.info("Summary analysis completed")
            return summary



    