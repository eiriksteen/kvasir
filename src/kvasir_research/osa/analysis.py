from uuid import UUID
from pathlib import Path
from typing import Dict, Tuple, OrderedDict, Literal, List
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models import ModelSettings

from kvasir_research.worker import logger
from kvasir_research.utils.agent_utils import get_model, get_dockerfile_for_env_description
from kvasir_research.history_processors import keep_only_most_recent_notebook
from kvasir_research.utils.code_utils import run_python_code_in_container, remove_print_statements_from_code
from kvasir_research.utils.redis_utils import save_analysis
from kvasir_research.utils.agent_utils import get_injected_analyses


ANALYSIS_SYSTEM_PROMPT = """
You are a professional data scientist, specialized in creating notebook-style analyses. 
You will be provided input data and a deliverable description, containing a goal or a question to answer with your analysis. 
It can be open-ended (conduct an EDA for basic insights) or specific (figure out exactly why this pattern leads to this outcome based on this data).
The analysis should follow a notebook-style approach. 

You will have the tools to:
- Create new code cells. 
- Execute code cells - NB: Include prints if you want to see outputs. We curently don't have support for showing you plots, make do with the terminal output.  
- Write markdown cells. This can be used for interpretation, explanation, planning, and more, before and after code cells. 

NB: 
We will concatenate all cells you execute into a single script, and when running a cell you will have access to the previous cells', but not the following cells', variables and functions. 
Keep this in mind for naming. 
Also, note that this differs from standard Jupyter, as you cannot run later cells and get their variables in earlier cells. 
Only prints in the current cell will be shown.
Keep your cells nice and atomic, exploit that you can use previous cells content. 

Be concise, precise, and specific in your analysis. 
It is crucial that the the analysis hits the deliverable description. 
Everything you do should have a purpose and clear goal, you should be ready to justify every code and markdown cell in terms of how they contribute to the deliverable. 
"""


@dataclass
class AnalysisDeps:
    run_id: str
    container_name: str
    orchestrator_id: UUID
    project_path: Path
    project_id: UUID
    data_paths: List[str]
    injected_analyses: List[str]
    time_limit: int  # Time limit in seconds
    # Key: name, value: (type, content), content is code, markdown, or output
    notebook: OrderedDict[str,
                          Tuple[Literal["code", "markdown", "output"], str]]


model = get_model()


analysis_agent = Agent[AnalysisDeps, str](
    model,
    deps_type=AnalysisDeps,
    retries=5,
    history_processors=[keep_only_most_recent_notebook],
    model_settings=ModelSettings(temperature=0)
)


@analysis_agent.system_prompt
async def analysis_system_prompt(ctx: RunContext[AnalysisDeps]) -> str:
    analyses_str = await get_injected_analyses(ctx.deps.injected_analyses)
    dockerfile_str = get_dockerfile_for_env_description()

    full_system_prompt = (
        f"{ANALYSIS_SYSTEM_PROMPT}\n\n" +
        f"Data paths: {ctx.deps.data_paths}\n\n" +
        f"You environment is described by the following Dockerfile:\n\n<dockerfile>\n{dockerfile_str}\n</dockerfile>\n\n" +
        f"Here are results from previous analyses:\n\n<analyses>\n{analyses_str}\n</analyses>"
    )

    return full_system_prompt


@analysis_agent.tool
async def create_or_replace_cell(ctx: RunContext[AnalysisDeps], content: str, name: str, cell_type: Literal["code", "markdown"]) -> str:
    logger.info(
        f"Analysis Agent [{ctx.deps.run_id}] create_or_replace_cell called: name={name}, cell_type={cell_type}, content_length={len(content)} chars")

    if cell_type == "code":
        past_code = _extract_code_from_previous_cells(ctx.deps.notebook, name)
        past_code_no_prints = remove_print_statements_from_code(past_code)
        full_code = f"{past_code_no_prints}\n\n{content}"
        out, err = await run_python_code_in_container(
            full_code,
            ctx.deps.container_name,
            truncate_output=True,
            timeout=ctx.deps.time_limit
        )

        logger.info(
            f"Analysis Agent [{ctx.deps.run_id}] executed code cell: {name}, output_length={len(out)} chars")

        if err:
            logger.error(
                f"Analysis Agent [{ctx.deps.run_id}] error executing code cell: {name}, error={err}")
            raise ModelRetry(f"Error executing code cell: {err}")

        ctx.deps.notebook[name] = (cell_type, content)
        ctx.deps.notebook[f"{name}_output"] = ("output", out)
    else:
        ctx.deps.notebook[name] = (cell_type, content)

    result = _notebook_to_string(ctx.deps.notebook, ctx.deps.run_id)
    logger.info(
        f"Analysis Agent [{ctx.deps.run_id}] create_or_replace_cell completed: name={name}, total_cells={len(ctx.deps.notebook)}")

    return result


@analysis_agent.tool
async def delete_cell(ctx: RunContext[AnalysisDeps], cell_name: str) -> str:
    logger.info(
        f"Analysis Agent [{ctx.deps.run_id}] delete_cell called: cell_name={cell_name}")

    del ctx.deps.notebook[cell_name]

    result = _notebook_to_string(ctx.deps.notebook, ctx.deps.run_id)
    logger.info(
        f"Analysis Agent [{ctx.deps.run_id}] delete_cell completed: cell_name={cell_name}, remaining_cells={len(ctx.deps.notebook)}")

    return result


@analysis_agent.output_validator
async def submit_results(ctx: RunContext[AnalysisDeps], summary: str) -> str:
    logger.info(
        f"Analysis Agent [{ctx.deps.run_id}] submit_results called: summary={summary}")
    logger.info(
        f"Analysis Agent [{ctx.deps.run_id}] submit_results called: notebook_cells={len(ctx.deps.notebook)}")

    # if no code cells, model retry
    if not any(cell_type == "code" for cell_type, _ in ctx.deps.notebook.values()):
        raise ModelRetry("You must submit code cells")

    if not ctx.deps.notebook:
        raise ModelRetry("Empty notebook, nothing to submit")

    result = _notebook_to_string(ctx.deps.notebook, ctx.deps.run_id)

    # Save analysis to Redis
    await save_analysis(ctx.deps.run_id, result)

    logger.info(
        f"Analysis Agent [{ctx.deps.run_id}] submit_results completed: notebook_cells={len(ctx.deps.notebook)}, saved to Redis")

    return result


###


def _extract_code_from_previous_cells(notebook: Dict[str, Tuple[str, str]], cell_name) -> str:

    code_cells = []
    for cell_name_in_notebook, (cell_type, content) in notebook.items():
        if cell_name_in_notebook == cell_name:
            break
        elif cell_type == "code":
            code_cells.append(content)

    return "\n\n".join(code_cells)


def _notebook_to_string(notebook: Dict[str, Tuple[str, str]], run_id: str) -> str:
    if not notebook:
        return f'<analysis run_id="{run_id}">\n  (empty notebook)\n</analysis>'

    result = [f'<analysis run_id="{run_id}">']

    for cell_name, (cell_type, content) in notebook.items():
        if cell_type == "markdown":
            result.append("")
            result.append(f'  <markdown name="{cell_name}">')
            # Indent content lines
            for line in content.strip().split("\n"):
                result.append(f"    {line}")
            result.append("  </markdown>")

        elif cell_type == "code":
            result.append("")
            result.append(f'  <code name="{cell_name}">')
            # Indent code lines
            for line in content.strip().split("\n"):
                result.append(f"    {line}")
            result.append("  </code>")

        elif cell_type == "output":
            result.append("")
            result.append("  <output>")
            # Indent output lines
            for line in content.strip().split("\n"):
                result.append(f"    {line}")
            result.append("  </output>")

    result.append("")
    result.append("</analysis>")

    return "\n".join(result)
