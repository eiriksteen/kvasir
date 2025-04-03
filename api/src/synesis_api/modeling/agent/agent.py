from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.settings import ModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from .prompt import MODEL_SYSTEM_PROMPT
from .deps import ModelDeps
from ...secrets import OPENAI_API_KEY, OPENAI_API_MODEL
from ..schema import ModelAgentOutput
from ...utils import run_code_in_container, copy_file_to_container

provider = OpenAIProvider(api_key=OPENAI_API_KEY)

model = OpenAIModel(
    model_name=OPENAI_API_MODEL,
    provider=provider
)

model_agent = Agent(
    model,
    result_type=ModelAgentOutput,
    deps_type=ModelDeps,
    name="Basic EDA Agent",
    model_settings=ModelSettings(
        temperature=0.1
    )
)


@model_agent.system_prompt
async def get_system_prompt(ctx: RunContext[ModelDeps]) -> str:
    _, err = await copy_file_to_container(ctx.deps.data_path, target_dir="/tmp")

    if err:
        raise ValueError(f"Error copying file to container: {err}")

    sys_prompt = (
        f"{MODEL_SYSTEM_PROMPT}\n"
        f"The problem description is as follows: {ctx.deps.problem_description}.\n"
        f"The data analysis: {ctx.deps.data_analysis}.\n"
        f"The path where the data is stored: /tmp/{ctx.deps.data_path.name}."
    )
    return sys_prompt


@model_agent.tool_plain
async def execute_python_code(python_code: str):
    """
    Execute a python code block.
    """
    out, err = await run_code_in_container(python_code)

    if err:
        raise ModelRetry(f"Error executing code: {err}")

    return out
