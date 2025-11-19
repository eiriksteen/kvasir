import uuid
import json
from typing import List
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext, ModelRetry

from kvasir_research.utils.agent_utils import get_model
from kvasir_ontology.entities.data_source.data_model import DataSourceDetailsCreate
from kvasir_ontology.entities.dataset.data_model import ObjectGroupCreate, ObjectGroup
from kvasir_ontology.entities.pipeline.data_model import PipelineImplementationCreate, PipelineRunCreate
from kvasir_ontology.entities.model.data_model import ModelImplementationCreate
from kvasir_ontology.visualization.data_model import EchartCreate
from kvasir_research.utils.code_utils import remove_print_statements_from_code
from kvasir_research.agents.v1.chart.agent import chart_agent
from kvasir_research.agents.v1.chart.deps import ChartDeps
from kvasir_research.agents.v1.chart.output import ChartAgentOutput
from kvasir_research.secrets import SANDBOX_INTERNAL_SCRIPT_DIR
from kvasir_research.agents.v1.extraction.deps import ExtractionDeps


data_source_system_prompt = f"""
Submit details (type_fields) to an existing data source. 
The data source ID will be provided in the prompt - you MUST use that ID.

Output the data source details as a Python dictionary, abiding by the following schema: 

{json.dumps(DataSourceDetailsCreate.model_json_schema())}

The output data to submit must be named 'data_source_details_dict'!

The dictionary must include:
- 'data_source_id': The UUID of the existing data source (provided in the prompt)
- 'type_fields': The type-specific fields for the data source (e.g., file metadata, schema information)

No hallucinations! Use code to extract the data source details, don't make it up. 
If you need to extract schema from a file, you can use:

```python
from io import StringIO
buffer = StringIO()
df.info(buf=buffer)
schema = buffer.getvalue()
head = df.head().to_string()
```
"""


async def submit_data_source_details(ctx: RunContext[ExtractionDeps], python_code: str) -> str:

    if "data_source_details_dict" not in python_code:
        raise ModelRetry(
            "The output data dictionary to submit must be named 'data_source_details_dict'!")
    try:
        python_code = remove_print_statements_from_code(python_code)
        submission_code, _ = await ctx.deps.ontology.data_sources.get_data_source_details_submission_code()
        full_code = f"{python_code}\n\n{submission_code}"
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"SANDBOX PROJECT ID: {ctx.deps.sandbox.project_id}"*10, "result")
        out, err = await ctx.deps.sandbox.run_python_code(full_code)

        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Data Source Details Submission Code:\n\n{full_code}", "result")
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Data Source Details Submission Output:\n\n{out}", "result")
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Data Source Details Submission Error:\n\n{err}", "error")

        if err:
            raise ModelRetry(f"Code execution error: {err}")

        return out.strip()

    except Exception as e:
        raise ModelRetry(
            f"Failed to submit data source details from code: {str(e)}")

data_source_agent = Agent[ExtractionDeps, str](
    model=get_model(),
    deps_type=ExtractionDeps,
    system_prompt=data_source_system_prompt,
    retries=3,
    output_type=submit_data_source_details
)


@data_source_agent.system_prompt
async def get_data_source_submission_code(ctx: RunContext[ExtractionDeps]) -> str:
    _, submission_desc = await ctx.deps.ontology.data_sources.get_data_source_details_submission_code()

    full_sys_prompt = (
        f"{data_source_system_prompt}\n\n" +
        "Your code must abide by the following description:\n\n" +
        f"{submission_desc}\n\n"
    )

    return full_sys_prompt


dataset_system_prompt = f"""
Submit object groups to an existing dataset. 
The dataset ID will be provided in the prompt - you MUST use that ID.

Dataset Hierarchy:
- Dataset: Collection of one or more object groups
- Object Group: Related data objects of the same modality (e.g., all time series, all images)

Chart Descriptions:
- You must provide a chart description for each object group you create, matched by the name field
- Example: ChartDescription(group_name="forecast_series", description="Line chart showing past values in blue, forecast values in green, ground-truth values in orange, and the forecast start point in a vertical line.")

Output the object groups as a Python dictionary or list of dictionaries, abiding by the following schema:

{json.dumps(ObjectGroupCreate.model_json_schema())}

The output data to submit must be named 'object_groups_dict'!
- If submitting a single object group, use a dictionary
- If submitting multiple object groups, use a list of dictionaries

No hallucinations! Use code to extract the object group metadata, don't make it up.
"""


class ChartDescription(BaseModel):
    group_name: str
    description: str


async def submit_object_groups(
    ctx: RunContext[ExtractionDeps],
    python_code: str,
    chart_descriptions: List[ChartDescription]
) -> str:
    if "object_groups_dict" not in python_code:
        raise ModelRetry(
            "The output data dictionary to submit must be named 'object_groups_dict'!")

    try:
        python_code = remove_print_statements_from_code(python_code)
        submission_code, _ = await ctx.deps.ontology.datasets.get_object_group_submission_code()
        full_code = f"{python_code}\n\n{submission_code}"
        out, err = await ctx.deps.sandbox.run_python_code(full_code)

        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Object Groups Submission Code:\n\n{full_code}", "result")
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Object Groups Submission Output:\n\n{out}", "result")
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Object Groups Submission Error:\n\n{err}", "error")

        if err:
            raise ModelRetry(f"Code execution error: {err}")

        result_data = json.loads(out.strip())

        if isinstance(result_data, list):
            object_groups = [ObjectGroup(**og_data) for og_data in result_data]
        else:
            object_groups = [ObjectGroup(**result_data)]

        chart_desc_map = {
            cd.group_name: cd.description for cd in chart_descriptions}

        missing_charts = [
            g.name for g in object_groups if g.name not in chart_desc_map]
        if missing_charts:
            raise ModelRetry(
                f"Missing chart descriptions for object groups: {', '.join(missing_charts)}. "
                "You must provide a ChartDescription for each object group."
            )

        for object_group in object_groups:
            chart_description = chart_desc_map[object_group.name]
            await _create_chart_for_object_group(
                ctx=ctx,
                object_group_id=object_group.id,
                chart_description=chart_description,
                datasets_to_inject=[],
                data_sources_to_inject=[]
            )

        if len(object_groups) == 1:
            return object_groups[0].model_dump_json(indent=4)
        else:
            return json.dumps([og.model_dump() for og in object_groups], indent=4, default=str)

    except Exception as e:
        raise ModelRetry(f"Failed to submit object groups from code: {str(e)}")


dataset_agent = Agent[ExtractionDeps, str](
    model=get_model(),
    deps_type=ExtractionDeps,
    system_prompt=dataset_system_prompt,
    retries=3,
    output_type=submit_object_groups
)


@dataset_agent.system_prompt
async def get_dataset_submission_code(ctx: RunContext[ExtractionDeps]) -> str:
    _, object_group_submission_desc = await ctx.deps.ontology.datasets.get_object_group_submission_code()

    full_sys_prompt = (
        f"{dataset_system_prompt}\n\n" +
        "Your code must abide by the following description:\n\n" +
        f"{object_group_submission_desc}\n\n"
    )

    return full_sys_prompt


pipeline_system_prompt = f"""
Submit a pipeline implementation to an existing pipeline.
The pipeline ID will be provided in the prompt - you MUST use that ID.

Output the pipeline implementation following this schema:

{json.dumps(PipelineImplementationCreate.model_json_schema())}

You may also include pipeline runs if applicable, following this schema:

{json.dumps(PipelineRunCreate.model_json_schema())}
"""


async def submit_pipeline_implementation(
    ctx: RunContext[ExtractionDeps],
    pipeline_implementation_create: PipelineImplementationCreate,
    runs: List[PipelineRunCreate] = []
) -> str:
    try:
        pipeline = await ctx.deps.ontology.pipelines.create_pipeline_implementation(pipeline_implementation_create)

        runs_output = []
        for run in runs:
            run.pipeline_id = pipeline.id
            run_obj = await ctx.deps.ontology.pipelines.create_pipeline_run(run)
            runs_output.append(run_obj.model_dump_json(indent=4))

        result = pipeline.model_dump_json(indent=4)
        if runs_output:
            result += "\n\nPipeline Runs:\n" + "\n\n".join(runs_output)

        return result

    except Exception as e:
        raise ModelRetry(f"Failed to submit pipeline implementation: {str(e)}")


pipeline_agent = Agent[ExtractionDeps, str](
    model=get_model(),
    deps_type=ExtractionDeps,
    system_prompt=pipeline_system_prompt,
    retries=3,
    output_type=submit_pipeline_implementation
)


model_system_prompt = f"""
Submit a model implementation to an existing model.
The model ID will be provided in the prompt - you MUST use that ID.

Output the model implementation following this schema:

{json.dumps(ModelImplementationCreate.model_json_schema())}
"""


async def submit_model_implementation(
    ctx: RunContext[ExtractionDeps],
    model_implementation_create: ModelImplementationCreate
) -> str:
    try:
        model = await ctx.deps.ontology.models.create_model_implementation(model_implementation_create)
        return model.model_dump_json(indent=4)

    except Exception as e:
        raise ModelRetry(f"Failed to submit model implementation: {str(e)}")


model_agent = Agent[ExtractionDeps, str](
    model=get_model(),
    deps_type=ExtractionDeps,
    system_prompt=model_system_prompt,
    retries=3,
    output_type=submit_model_implementation
)


###


async def _create_chart_for_object_group(
    ctx: RunContext[ExtractionDeps],
    object_group_id: uuid.UUID,
    chart_description: str,
    datasets_to_inject: List[uuid.UUID],
    data_sources_to_inject: List[uuid.UUID],
) -> ChartAgentOutput:

    try:
        object_group = await ctx.deps.ontology.datasets.get_object_group(object_group_id)
    except Exception as e:
        raise ModelRetry(
            f"Failed to get object group. The ID must be the DB UUID of the group: {str(e)}")

    chart_result = await chart_agent.run(
        chart_description,
        deps=ChartDeps(
            user_id=ctx.deps.user_id,
            project_id=ctx.deps.project_id,
            package_name=ctx.deps.package_name,
            sandbox_type=ctx.deps.sandbox_type,
            callbacks=ctx.deps.callbacks,
            datasets_injected=datasets_to_inject,
            data_sources_injected=data_sources_to_inject,
            object_group=object_group,
            bearer_token=ctx.deps.bearer_token
        )
    )
    save_path = SANDBOX_INTERNAL_SCRIPT_DIR / f"{object_group_id}.py"
    await ctx.deps.sandbox.write_file(save_path, chart_result.output.script_content)
    await ctx.deps.ontology.datasets.create_object_group_echart(
        object_group_id,
        EchartCreate(chart_script_path=str(save_path))
    )

    return chart_result.output
