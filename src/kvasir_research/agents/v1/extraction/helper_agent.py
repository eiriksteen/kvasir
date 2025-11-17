import uuid
import json
from typing import List, Literal
from pydantic import BaseModel
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext, ModelRetry

from kvasir_research.utils.agent_utils import get_model
from kvasir_ontology.entities.data_source.data_model import DataSourceCreate
from kvasir_ontology.entities.dataset.data_model import DatasetCreate, DataObjectCreate, Dataset, ObjectGroupCreate, ObjectGroup
from kvasir_ontology.entities.pipeline.data_model import PipelineImplementationCreate, PipelineRunCreate, PipelineCreate
from kvasir_ontology.entities.model.data_model import ModelInstantiatedCreate, ModelImplementationCreate, ModelCreate
from kvasir_ontology.graph.data_model import EdgeDefinition
from kvasir_ontology.visualization.data_model import EchartCreate
from kvasir_research.utils.code_utils import remove_print_statements_from_code
from kvasir_research.agents.v1.chart.agent import chart_agent
from kvasir_research.agents.v1.chart.deps import ChartDeps
from kvasir_research.agents.v1.chart.output import ChartAgentOutput
from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks
from kvasir_research.sandbox.local import LocalSandbox
from kvasir_research.sandbox.modal import ModalSandbox
from kvasir_research.sandbox.abstract import AbstractSandbox
from kvasir_research.secrets import SANDBOX_INTERNAL_SCRIPT_DIR


@dataclass
class HelperDeps:
    run_id: uuid.UUID
    project_id: uuid.UUID
    package_name: str
    callbacks: KvasirV1Callbacks
    sandbox: AbstractSandbox
    sandbox_type: Literal["local", "modal"] = "local"

    def __post_init__(self):
        if self.sandbox_type == "local":
            self.sandbox = LocalSandbox(self.project_id, self.package_name)
        elif self.sandbox_type == "modal":
            self.sandbox = ModalSandbox(self.project_id, self.package_name)
        else:
            raise ValueError(f"Invalid sandbox type: {self.sandbox_type}")


data_source_system_prompt = f"""
Submit metadata about a data source associated with a codebase. 
The source can be a file, a database, a cloud storage, etc. 
Output metadata about the source as a Python dictionary, abiding by the following schema: 

{json.dumps(DataSourceCreate.model_json_schema())}

The output data to submit must be named 'data_source_dict'!

IMPORTANT: If a target entity ID is provided in the prompt, you MUST include 'data_source_id' in the dictionary with that UUID value.
When 'data_source_id' is present, you should ONLY submit the type_fields (details) for that existing data source.
Otherwise, create a new data source with full metadata (without data_source_id field).

No hallucinations! Use code to extract the data source metadata, don't make it up. 
If you need to extract schema from a file, you can use:

```python
from io import StringIO
buffer = StringIO()
df.info(buf=buffer)
schema = buffer.getvalue()
head = df.head().to_string()
```
"""


async def submit_data_source(ctx: RunContext[HelperDeps], python_code: str) -> str:

    if "data_source_dict" not in python_code:
        raise ModelRetry(
            "The output data dictionary to submit must be named 'data_source_dict'!")
    try:
        python_code = remove_print_statements_from_code(python_code)
        submission_code, _ = await ctx.deps.callbacks.ontology.data_sources.get_data_source_submission_code()
        full_code = f"{python_code}\n\n{submission_code}"
        out, err = await ctx.deps.sandbox.run_python_code(full_code)

        await ctx.deps.callbacks.log(ctx.deps.run_id, f"Data Source Submission Code:\n\n{full_code}", "result")
        await ctx.deps.callbacks.log(ctx.deps.run_id, f"Data Source Submission Output:\n\n{out}", "result")
        await ctx.deps.callbacks.log(ctx.deps.run_id, f"Data Source Submission Error:\n\n{err}", "error")

        if err:
            raise ModelRetry(f"Code execution error: {err}")

        return out.strip()

    except Exception as e:
        raise ModelRetry(
            f"Failed to submit data source from code: {str(e)}")

data_source_agent = Agent[HelperDeps, str](
    model=get_model(),
    deps_type=HelperDeps,
    system_prompt=data_source_system_prompt,
    retries=3,
    output_type=submit_data_source
)


@data_source_agent.system_prompt
async def get_data_source_submission_code(ctx: RunContext[HelperDeps]) -> str:
    _, submission_desc = await ctx.deps.callbacks.ontology.data_sources.get_data_source_submission_code()

    full_sys_prompt = (
        f"{data_source_system_prompt}\n\n" +
        "Your code must abide by the following description:\n\n" +
        f"{submission_desc}\n\n"
    )

    return full_sys_prompt


# TODO: fill
dataset_system_prompt = f"""
Submit metadata about a dataset with its object groups and data objects, derived from data sources or pipelines. 

Dataset Hierarchy:
- Dataset: Collection of one or more object groups
- Object Group: Related data objects of the same modality (e.g., all time series, all images)
- Data Object: Individual samples (one time series, one image, one document)

Chart Descriptions:
- You must provide a chart description for each object group in the dataset, matched by the name field
- Example: ChartDescription(group_name="forecast_series", description="Line chart showing past values in blue, forecast values in green, ground-truth values in orange, and the forecast start point in a vertical line.")

IMPORTANT: If a target entity ID is provided in the prompt, you MUST include 'dataset_id' in the dictionary with that UUID value.
When 'dataset_id' is present, you should add object groups to that existing dataset (not create a new dataset).
Otherwise, create a new dataset with full metadata (without dataset_id field). 

No hallucinations! Use code to extract the dataset metadata, don't make it up. 

You will either submit a whole dataset, or submit object groups and/or files to an existing dataset. 

The dataset schema is:
{json.dumps(DatasetCreate.model_json_schema())}

The object group schema is:
{json.dumps(ObjectGroupCreate.model_json_schema())}

The data object schema is:
{json.dumps(DataObjectCreate.model_json_schema())}
"""


class ChartDescription(BaseModel):
    group_name: str
    description: str


async def submit_dataset(
    ctx: RunContext[HelperDeps],
    python_code: str,
    chart_descriptions: List[ChartDescription]
) -> str:

    try:
        python_code = remove_print_statements_from_code(python_code)
        submission_code, _ = await ctx.deps.callbacks.ontology.datasets.get_dataset_submission_code()
        full_code = f"{python_code}\n\n{submission_code}"
        out, err = await ctx.deps.sandbox.run_python_code(full_code)

        await ctx.deps.callbacks.log(ctx.deps.run_id, f"Dataset Submission Code:\n\n{full_code}", "result")
        await ctx.deps.callbacks.log(ctx.deps.run_id, f"Dataset Submission Output:\n\n{out}", "result")
        await ctx.deps.callbacks.log(ctx.deps.run_id, f"Dataset Submission Error:\n\n{err}", "error")

        if err:
            raise ModelRetry(f"Code execution error: {err}")

        result_data = json.loads(out.strip())
        result_obj = Dataset(**result_data)

        # Create mapping of group names to chart descriptions
        chart_desc_map = {
            cd.group_name: cd.description for cd in chart_descriptions}

        # Verify we have chart descriptions for all object groups
        missing_charts = [
            g.name for g in result_obj.object_groups if g.name not in chart_desc_map]
        if missing_charts:
            raise ModelRetry(
                f"Missing chart descriptions for object groups: {', '.join(missing_charts)}. "
                "You must provide a ChartDescription for each object group in the dataset."
            )

        # Automatically dispatch chart agent for each object group using the DB IDs
        for object_group in result_obj.object_groups:
            chart_description = chart_desc_map[object_group.name]
            await _create_chart_for_object_group(
                ctx=ctx,
                object_group_id=object_group.id,
                chart_description=chart_description,
                datasets_to_inject=[result_obj.id],
                data_sources_to_inject=[]
            )

        return result_obj.model_dump_json(indent=4)

    except Exception as e:
        raise ModelRetry(f"Failed to submit dataset from code: {str(e)}")


async def submit_object_groups(
    ctx: RunContext[HelperDeps],
    python_code: str,
    chart_descriptions: List[ChartDescription]
) -> str:
    try:
        python_code = remove_print_statements_from_code(python_code)
        submission_code, _ = await ctx.deps.callbacks.ontology.datasets.get_object_group_submission_code()
        full_code = f"{python_code}\n\n{submission_code}"
        out, err = await ctx.deps.sandbox.run_python_code(full_code)

        await ctx.deps.callbacks.log(ctx.deps.run_id, f"Object Groups Submission Code:\n\n{full_code}", "result")
        await ctx.deps.callbacks.log(ctx.deps.run_id, f"Object Groups Submission Output:\n\n{out}", "result")
        await ctx.deps.callbacks.log(ctx.deps.run_id, f"Object Groups Submission Error:\n\n{err}", "error")

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


dataset_agent = Agent[HelperDeps, str](
    model=get_model(),
    deps_type=HelperDeps,
    system_prompt=dataset_system_prompt,
    retries=3,
    output_type=[submit_dataset, submit_object_groups]
)


@dataset_agent.system_prompt
async def get_dataset_submission_code(ctx: RunContext[HelperDeps]) -> str:
    _, dataset_submission_desc = await ctx.deps.callbacks.ontology.datasets.get_dataset_submission_code()
    _, object_group_submission_desc = await ctx.deps.callbacks.ontology.datasets.get_object_group_submission_code()

    full_sys_prompt = (
        f"{dataset_system_prompt}\n\n" +
        "For dataset submission, your code must abide by the following description:\n\n" +
        f"{dataset_submission_desc}\n\n" +
        "For object group submission, your code must abide by the following description:\n\n" +
        f"{object_group_submission_desc}\n\n"
    )

    return full_sys_prompt


pipeline_system_prompt = """
Submit metadata about a data processing or machine learning pipeline. 
It will either be an implementation, in which case you will associate it with an existing pipeline, or a new pipeline, where you will create the base pipeline. 
In the latter case you should also submit the implementation and any associated runs if possible. 
"""


async def submit_pipeline(ctx: RunContext[HelperDeps], pipeline_create: PipelineCreate, edges: List[EdgeDefinition]) -> str:
    try:
        pipeline_obj = await ctx.deps.callbacks.ontology.insert_pipeline(pipeline_create, edges)
    except Exception as e:
        raise ModelRetry(f"Failed to submit pipeline: {str(e)}")

    return pipeline_obj.model_dump_json(indent=4)


async def submit_pipeline_implementation(
    ctx: RunContext[HelperDeps],
    pipeline_implementation_create: PipelineImplementationCreate,
    runs: List[PipelineRunCreate]
) -> str:
    """
    Submit a pipeline. 
    This can be associated with a current pipeline, in which case you should submit the implementation and possible runs. 
    If this is a brand new pipeline entity, you must include the pipeline_create object as well.
    """
    out_str = ""
    try:
        pipeline_implementation = await ctx.deps.callbacks.ontology.pipelines.create_pipeline_implementation(pipeline_implementation_create)
        out_str += f"Pipeline implementation created: {pipeline_implementation.model_dump_json(indent=4)}\n\n"
        for run in runs:
            run.pipeline_id = pipeline_implementation.id
            pipe_run_obj = await ctx.deps.callbacks.ontology.pipelines.create_pipeline_run(run)
            out_str += f"Pipeline run created: {pipe_run_obj.model_dump_json(indent=4)}\n\n"

    except Exception as e:
        raise ModelRetry(f"Failed to submit pipeline implementation: {str(e)}")

    return out_str


pipeline_agent = Agent[HelperDeps, str](
    model=get_model(),
    deps_type=HelperDeps,
    system_prompt=pipeline_system_prompt,
    retries=3,
    output_type=[submit_pipeline, submit_pipeline_implementation]
)


model_system_prompt = """
Submit metadata about a model, which can be a machine learning model, a rule-based model, an optimization model, etc. 
It will either be an implementation, in which case you will associate it with an existing model, or a new model instantiated.
The instantiated model is a model that is configured and ready to be used. 
You may have to create the base model and/or its implementation in the same go. 
"""


async def submit_model_instantiated(ctx: RunContext[HelperDeps], model_instantiated_create: ModelInstantiatedCreate, edges: List[EdgeDefinition]) -> str:
    try:
        model_instantiated_obj = await ctx.deps.callbacks.ontology.insert_model_instantiated(model_instantiated_create, edges)
    except Exception as e:
        raise ModelRetry(f"Failed to submit model: {str(e)}")
    return model_instantiated_obj.model_dump_json(indent=4)


async def submit_model_implementation(ctx: RunContext[HelperDeps], model_implementation_create: ModelImplementationCreate) -> str:
    try:
        model_implementation_obj = await ctx.deps.callbacks.ontology.models.create_model_implementation(model_implementation_create)
    except Exception as e:
        raise ModelRetry(f"Failed to submit model implementation: {str(e)}")
    return model_implementation_obj.model_dump_json(indent=4)


model_agent = Agent[HelperDeps, str](
    model=get_model(),
    deps_type=HelperDeps,
    system_prompt=model_system_prompt,
    retries=3,
    output_type=[submit_model_instantiated, submit_model_implementation]
)


###


async def _create_chart_for_object_group(
    ctx: RunContext[HelperDeps],
    object_group_id: uuid.UUID,
    chart_description: str,
    datasets_to_inject: List[uuid.UUID],
    data_sources_to_inject: List[uuid.UUID],
) -> ChartAgentOutput:

    try:
        object_group = await ctx.deps.callbacks.ontology.datasets.get_object_group(object_group_id)
    except Exception as e:
        raise ModelRetry(
            f"Failed to get object group. The ID must be the DB UUID of the group: {str(e)}")

    chart_result = await chart_agent.run(
        chart_description,
        deps=ChartDeps(
            callbacks=ctx.deps.callbacks,
            project_id=ctx.deps.project_id,
            package_name=ctx.deps.package_name,
            sandbox_type=ctx.deps.sandbox_type,
            datasets_injected=datasets_to_inject,
            data_sources_injected=data_sources_to_inject,
            object_group=object_group
        )
    )
    save_path = SANDBOX_INTERNAL_SCRIPT_DIR / f"{object_group_id}.py"
    await ctx.deps.sandbox.write_file(save_path, chart_result.output.script_content)
    await ctx.deps.callbacks.ontology.datasets.create_object_group_echart(
        object_group_id,
        EchartCreate(chart_script_path=str(save_path))
    )

    return chart_result.output
