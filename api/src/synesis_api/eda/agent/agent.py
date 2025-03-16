import pandas as pd
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.settings import ModelSettings
from pathlib import Path
from dataclasses import dataclass
from .tools import eda_cs_basic_tools, eda_cs_advanced_tools
from .prompt import EDA_SYSTEM_PROMPT
from .deps import EDADepsBasic, EDADepsAdvanced, EDADepsIndependent, EDADepsSummary
from ...secrets import OPENAI_API_KEY, OPENAI_API_MODEL
from ...ontology.schema import DataModelBase
from ..schema import EDAResponse, EDAResponseWithCode
from ...utils import run_code_in_container, copy_file_to_container

model = OpenAIModel(
    model_name=OPENAI_API_MODEL,
    api_key=OPENAI_API_KEY
)

eda_basic_agent = Agent(
    model,
    result_type=EDAResponse,
    system_prompt=EDA_SYSTEM_PROMPT,
    deps_type=EDADepsBasic,
    name="Basic EDA Agent",
    model_settings=ModelSettings(
        temperature=0.1
    ),
    tools=eda_cs_basic_tools
)

eda_advanced_agent = Agent(
    model,
    result_type=EDAResponse,
    deps_type=EDADepsAdvanced,
    name="Advanced EDA Agent",
    model_settings=ModelSettings(
        temperature=0.1
    ),
    tools=eda_cs_advanced_tools
)

eda_independent_agent = Agent(
    model,
    result_type=EDAResponseWithCode,
    deps_type=EDADepsIndependent,
    name="Independent EDA Agent",
    model_settings=ModelSettings(
        temperature=0.1
    ),
)

eda_summary_agent = Agent(
    model,
    result_type=EDAResponseWithCode,
    deps_type=EDADepsSummary,
    name="Summary EDA Agent",
    model_settings=ModelSettings(
        temperature=0.1
    ),
)


@eda_advanced_agent.system_prompt
async def get_system_prompt(ctx: RunContext[EDADepsAdvanced]) -> str:
    sys_prompt = (
        f"{EDA_SYSTEM_PROMPT}\n"
        f"The problem description is as follows: {ctx.deps.problem_description}\n"
        f"The data description is as follows: {ctx.deps.data_description}\n"
        f"The result from the basic data analysis: {ctx.deps.basic_data_analysis}"
    )
    return sys_prompt


@eda_independent_agent.system_prompt
async def get_system_prompt(ctx: RunContext[EDADepsIndependent]) -> str:
    _, err = await copy_file_to_container(ctx.deps.data_path, target_dir="/tmp")

    if err:
        raise ValueError(f"Error copying file to container: {err}")

    sys_prompt = (
        f"{EDA_SYSTEM_PROMPT}\n"
        f"The problem description is as follows: {ctx.deps.problem_description}\n"
        f"The data description is as follows: {ctx.deps.data_description}\n"
        f"The result from the basic data analysis: {ctx.deps.basic_data_analysis}\n"
        f"The result from the advanced data analysis: {ctx.deps.advanced_data_analysis}"
        # must input where the file is stored
    )
    return sys_prompt

# @eda_independent_agent.tool_plain
# async def execute_python_code(python_code: str):
#     """
#     Execute a python code block.
#     """
#     out, err = await run_code_in_container(python_code)

#     if err:
#         raise ModelRetry(f"Error executing code: {err}")

#     return out


@eda_summary_agent.system_prompt
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