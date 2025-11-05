from pydantic import BaseModel
from pydantic_ai import RunContext, ModelRetry

from project_server.agents.chart.deps import ChartDeps
from project_server.utils.code_utils import run_python_code_in_container, remove_print_statements_from_code
from project_server.worker import logger


class ChartAgentOutput(BaseModel):
    script_content: str


async def submit_chart(
    ctx: RunContext[ChartDeps],
    python_code: str
) -> ChartAgentOutput:
    """
    Submit a chart generation function. It must be called generate_chart.

    If the chart code is for an object group, the function will be called with the sample_object_id as a parameter.
    If the chart code is for a standalone chart, the function will be called with no parameters.

    Returns the code and function name that can be used to execute the chart.
    """
    try:
        python_code = remove_print_statements_from_code(python_code)

        if "generate_chart" not in python_code:
            raise ModelRetry(
                "generate_chart function is not defined in the code")

        # Build validation code with optional base_code prepended
        validation_parts = []
        if ctx.deps.base_code:
            validation_parts.append(ctx.deps.base_code)

        validation_parts.append(python_code)
        validation_parts.extend([
            "from synesis_schemas.project_server import EChartsOption",
        ])

        # Determine function call based on whether we have an object group
        if ctx.deps.object_group is not None:
            validation_parts.append(
                f"result = generate_chart('{ctx.deps.object_group.first_data_object.original_id}')")
        else:
            # Standalone chart - no parameters
            validation_parts.append(f"result = generate_chart()")

        # Validate inside the sandbox
        # Validate directly with full schema - allows LLM to add any valid extras
        validation_code = "\n".join(
            validation_parts + ["EChartsOption(**result)"])
        out, err = await run_python_code_in_container(validation_code, ctx.deps.container_name)
        out_code = "\n".join(validation_parts +
                             ["import json", "print(json.dumps(result, default=str))"])

        logger.info("="*100)
        logger.info("SUBMIT CHART FUNCTION CODE")
        logger.info(out_code)
        logger.info("OUT")
        logger.info(out)
        logger.info("ERR")
        err_truncated = err[:2000] + \
            ("[THE REST OF THE ERROR WAS TRUNCATED]" if len(err) > 2000 else "")
        logger.info(err_truncated)
        logger.info("="*100)

        if err:
            raise ModelRetry(f"Code execution error: {err_truncated}")

        return ChartAgentOutput(script_content=out_code)

    except Exception as e:
        raise ModelRetry(f"Failed to submit chart function: {str(e)}")
