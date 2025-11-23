import uuid
import json
from typing import List, Optional
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext, ModelRetry, ModelSettings

from kvasir_research.utils.agent_utils import get_model
from kvasir_ontology.entities.data_source.data_model import DataSourceDetailsCreate
from kvasir_ontology.entities.dataset.data_model import ObjectGroupCreate, ObjectGroup, DataObjectCreate
from kvasir_ontology.entities.pipeline.data_model import PipelineImplementationCreate, PipelineRunCreate
from kvasir_ontology.entities.model.data_model import ModelImplementationCreate, ModelInstantiatedCreate
from kvasir_ontology.visualization.data_model import EchartCreate
from kvasir_research.utils.code_utils import remove_print_statements_from_code
from kvasir_research.agents.v1.chart.agent import chart_agent
from kvasir_research.agents.v1.chart.deps import ChartDeps
from kvasir_research.agents.v1.chart.output import ChartAgentOutput
from kvasir_research.agents.v1.extraction.deps import ExtractionDeps
from kvasir_research.secrets import SANDBOX_INTERNAL_SCRIPT_DIR
from kvasir_research.agents.v1.shared_tools import navigation_toolset


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
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Submitting data source details ({len(python_code)} characters)", "tool_call")

    if "data_source_details_dict" not in python_code:
        raise ModelRetry(
            "The output data dictionary to submit must be named 'data_source_details_dict'!")
    try:
        python_code = remove_print_statements_from_code(python_code)
        submission_code, _ = await ctx.deps.ontology.data_sources.get_data_source_details_submission_code()
        full_code = f"{python_code}\n\n{submission_code}"
        out, err = await ctx.deps.sandbox.run_python_code(full_code)

        if err:
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Data source details submission error: {err[:500]}", "error")
        else:
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Data source details submitted successfully (output: {len(out)} characters)", "result")

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
    toolsets=[navigation_toolset],
    model_settings=ModelSettings(temperature=0),
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
- Data Object: Individual samples (one time series, one image, one document, etc.)

Chart Descriptions:
- You must provide a chart description for each object group you create, matched by the name field
- Example: ChartDescription(group_name="forecast_series", description="Line chart showing past values in blue, forecast values in green, ground-truth values in orange, and the forecast start point in a vertical line.")

Output the object groups as a Python dictionary or list of dictionaries, abiding by the following schema:

{json.dumps(ObjectGroupCreate.model_json_schema())}

The output data to submit must be named 'object_groups_dict'!
- If submitting a single object group, use a dictionary
- If submitting multiple object groups, use a list of dictionaries

DataFrames Structure:
Each DataFrame row represents ONE data object (e.g., one time series, one image, one document).
Each row must follow the DataObjectCreate schema:

{json.dumps(DataObjectCreate.model_json_schema())}

The DataFrame must have columns matching the DataObjectCreate schema:
- Base fields: 'name', 'original_id', 'description' (optional)
- 'modality_fields': A dictionary column containing modality-specific metadata
  The structure of modality_fields depends on the modality type (time_series, tabular, etc.)
  and must match the corresponding Create schema (TimeSeriesCreate, TabularRowCreate, etc.)

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
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Submitting object groups ({len(python_code)} characters, {len(chart_descriptions)} chart description(s))", "tool_call")

    if "object_groups_dict" not in python_code:
        raise ModelRetry(
            "The output data dictionary to submit must be named 'object_groups_dict'!")

    if "dataframes_dict" not in python_code:
        raise ModelRetry(
            "The 'dataframes_dict' variable must be created in the code to map filenames to DataFrames!")

    try:
        python_code = remove_print_statements_from_code(python_code)
        submission_code, _ = await ctx.deps.ontology.datasets.get_object_group_submission_code()
        full_code = f"{python_code}\n\n{submission_code}"
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Running object group submission code:\n\n{full_code}", "result")
        out, err = await ctx.deps.sandbox.run_python_code(full_code)

        if err:
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Object groups submission error: {err[:500]}", "error")
        else:
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Object groups submitted successfully (output: {len(out)} characters)", "result")

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
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Creating chart for object group: {object_group.name}", "result")
            await _create_chart_for_object_group(
                ctx=ctx,
                object_group_id=object_group.id,
                chart_description=chart_description,
                datasets_to_inject=[],
                data_sources_to_inject=[]
            )

        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Completed submitting {len(object_groups)} object group(s) with charts", "result")
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
    toolsets=[navigation_toolset],
    model_settings=ModelSettings(temperature=0),
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
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Submitting pipeline implementation: {pipeline_implementation_create.python_function_name}", "tool_call")
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

        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Pipeline implementation submitted successfully ({len(runs)} run(s))", "result")
        return result

    except Exception as e:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Error submitting pipeline implementation: {str(e)}", "error")
        raise ModelRetry(f"Failed to submit pipeline implementation: {str(e)}")


pipeline_agent = Agent[ExtractionDeps, str](
    model=get_model(),
    deps_type=ExtractionDeps,
    system_prompt=pipeline_system_prompt,
    toolsets=[navigation_toolset],
    model_settings=ModelSettings(temperature=0),
    retries=3,
    output_type=submit_pipeline_implementation
)


class ModelAgentOutput(BaseModel):
    model_implementation: Optional[ModelImplementationCreate] = None
    instantiations: List[ModelInstantiatedCreate] = []


model_system_prompt = f"""
Submit model implementation details and configure all instantiations for an existing model.
The model ID and instantiation information will be provided in the prompt - you MUST use those IDs.

You must:
1. Submit the model implementation (if not already submitted) following this schema:
{json.dumps(ModelImplementationCreate.model_json_schema())}

2. Configure ALL instantiations with their specific details. For each instantiation, provide:
   - config: The configuration dictionary for that specific instantiation
   - weights_save_dir: Path to where model weights are saved (if applicable)
   - Any other relevant details

Output format:
- model_implementation: The ModelImplementationCreate object (or None if already submitted)
- instantiations: A list of ModelInstantiatedCreate objects, one for each instantiation
  Each must have model_id set (not model_create) and include the specific config and weights_save_dir for that instantiation.

The instantiations list should follow this schema:
{json.dumps(ModelInstantiatedCreate.model_json_schema())}

IMPORTANT: 
- Extract config and weights_save_dir from code files for each instantiation
- Each instantiation may have different configs (e.g., different hyperparameters, different training data)
- Use the instantiation names and IDs provided in the prompt to match them correctly
"""


async def submit_model_implementation_and_instantiations(
        ctx: RunContext[ExtractionDeps],
        output: ModelAgentOutput) -> str:

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Submitting model details: implementation={'yes' if output.model_implementation else 'no'}, instantiations={len(output.instantiations)}", "tool_call")

    results = []

    if output.model_implementation:
        try:
            model = await ctx.deps.ontology.models.create_model_implementation(output.model_implementation)
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Model implementation submitted: {output.model_implementation.python_class_name}", "result")
            results.append(
                f"Model Implementation:\n{model.model_dump_json(indent=2)}")
        except Exception as e:
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Error submitting model implementation: {str(e)}", "error")
            raise ModelRetry(
                f"Failed to submit model implementation: {str(e)}")

    instantiation_results = []
    for i, instantiation in enumerate(output.instantiations, 1):
        try:
            await ctx.deps.callbacks.log(
                ctx.deps.user_id,
                ctx.deps.run_id,
                f"Instantiation {i}/{len(output.instantiations)}: {instantiation.name} - config keys: {list(instantiation.config.keys()) if instantiation.config else 'empty'}, weights_save_dir: {instantiation.weights_save_dir}",
                "result"
            )
            instantiation_results.append(
                f"Instantiation {instantiation.name}: config={json.dumps(instantiation.config, indent=2)}, weights_save_dir={instantiation.weights_save_dir}")
        except Exception as e:
            await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Error processing instantiation {instantiation.name}: {str(e)}", "error")
            raise ModelRetry(
                f"Failed to process instantiation {instantiation.name}: {str(e)}")

    if instantiation_results:
        results.append("\nInstantiations:\n" +
                       "\n\n".join(instantiation_results))

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, "Model details submitted successfully", "result")
    return "\n\n".join(results) if results else "Model details processed (no changes needed)"


model_agent = Agent[ExtractionDeps, ModelAgentOutput](
    model=get_model(),
    deps_type=ExtractionDeps,
    system_prompt=model_system_prompt,
    toolsets=[navigation_toolset],
    model_settings=ModelSettings(temperature=0),
    retries=3,
    output_type=submit_model_implementation_and_instantiations
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
