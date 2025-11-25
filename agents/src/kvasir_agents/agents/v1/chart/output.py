import json
from pydantic import BaseModel
from pydantic_ai import RunContext, ModelRetry

from kvasir_agents.agents.v1.chart.deps import ChartDeps
from kvasir_agents.utils.code_utils import remove_print_statements_from_code
from kvasir_ontology.visualization.data_model import EChartsOption


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
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Submitting chart code ({len(python_code)} characters)", "tool_call")
    try:
        python_code = remove_print_statements_from_code(python_code)

        if "generate_chart" not in python_code:
            raise ModelRetry(
                "generate_chart function is not defined in the code")

        if ctx.deps.base_code:
            base_code = remove_print_statements_from_code(ctx.deps.base_code)
            python_code = f"{base_code}\n\n{python_code}"

        # validation parts

        # Determine function call based on whether we have an object group
        if ctx.deps.object_group is not None:
            validation_code = f"{python_code}\n\nresult = generate_chart('{ctx.deps.object_group.first_data_object.original_id}')"
        else:
            # Standalone chart - no parameters
            validation_code = f"{python_code}\n\nresult = generate_chart()"

        # Validate inside the sandbox
        # Suppress warnings and ensure clean JSON output
        validation_code = f"{validation_code}\n\nimport json\nimport warnings\nwarnings.filterwarnings('ignore')\nprint(json.dumps(result, default=str))"

        out, err = await ctx.deps.sandbox.run_python_code(validation_code)

        err_truncated = err[:2000] + \
            ("[THE REST OF THE ERROR WAS TRUNCATED]" if len(err) > 2000 else "")

        if err:
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Chart code execution error: {err_truncated}", "error")
            raise ModelRetry(f"Code execution error: {err_truncated}")

        try:
            result_data = json.loads(out.strip())
            EChartsOption(**result_data)
        except json.JSONDecodeError as e:
            out_preview = out[:1000] + ("..." if len(out) > 1000 else "")
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Error parsing chart result: {str(e)}\nOutput preview: {out_preview}", "error")
            raise ModelRetry(
                f"Failed to parse chart result: {str(e)}. Output preview: {out_preview[:200]}")
        except Exception as e:
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Error validating chart result: {str(e)}", "error")
            raise ModelRetry(f"Failed to validate chart result: {str(e)}.")

        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, "Chart code validated and submitted successfully", "result")
        return ChartAgentOutput(script_content=python_code)

    except Exception as e:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Error submitting chart: {str(e)}", "error")
        raise ModelRetry(f"Failed to submit chart function: {str(e)}")
