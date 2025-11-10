import uuid
import json
from typing import List
from pydantic import BaseModel
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext, ModelRetry

from project_server.utils.agent_utils import get_model
from project_server.client import ProjectClient
from synesis_schemas.main_server import (
    DataSourceCreate,
    Project,
    Dataset,
    ObjectGroupEChartCreate,
    DatasetCreate,
    DataObjectCreate,
    PipelineImplementationCreate,
    PipelineRunCreate,
    ModelEntityImplementationCreate,
    AddEntityToProject
)
from project_server.utils.code_utils import run_python_code_in_container, remove_print_statements_from_code
from project_server.agents.chart.agent import chart_agent
from project_server.agents.chart.deps import ChartDeps
from project_server.agents.chart.output import ChartAgentOutput
from project_server.app_secrets import AGENT_OUTPUTS_INTERNAL_DIR
from project_server.utils.docker_utils import write_file_to_container
from project_server.client.requests.project import post_add_entity
from project_server.client.requests.data_objects import create_object_group_echart, get_object_group
from project_server.client.requests.pipeline import post_pipeline_implementation, post_pipeline_run
from project_server.client.requests.model import post_model_entity_implementation
from project_server.worker import logger


@dataclass
class HelperDeps:
    client: ProjectClient
    bearer_token: str
    project: Project
    container_name: str


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
        submission_code = (
            f"{python_code}\n"
            "import asyncio\n"
            "from project_server.client import ProjectClient\n"
            "from project_server.client.requests.data_sources import post_data_source, post_data_source_details\n"
            "from project_server.client.requests.project import post_add_entity\n"
            "from synesis_schemas.main_server import DataSourceCreate, DataSourceDetailsCreate, AddEntityToProject\n"
            "from uuid import UUID\n"
            "import json\n"
            "\n"
            "async def run_submission():\n"
            f"    client = ProjectClient(bearer_token='{ctx.deps.bearer_token}')\n"
            "    # Check if this is updating an existing data source or creating a new one\n"
            "    if 'data_source_id' in data_source_dict:\n"
            "        # Update existing data source with details\n"
            "        details_request = DataSourceDetailsCreate(**data_source_dict)\n"
            "        result = await post_data_source_details(client, details_request)\n"
            "    else:\n"
            "        # Create new data source\n"
            "        request = DataSourceCreate(**data_source_dict)\n"
            "        result = await post_data_source(client, request)\n"
            "        # Add data source to project\n"
            "        add_entity_request = AddEntityToProject(\n"
            f"            project_id=UUID('{ctx.deps.project.id}'),\n"
            "            entity_type='data_source',\n"
            "            entity_id=result.id\n"
            "        )\n"
            "        await post_add_entity(client, add_entity_request)\n"
            "    print(json.dumps(result.model_dump(), default=str))\n"
            "\n"
            "asyncio.run(run_submission())"
        )
        out, err = await run_python_code_in_container(submission_code, ctx.deps.container_name)

        if err:
            raise ValueError(f"Code execution error: {err}")

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


# TODO: fill
dataset_system_prompt = f"""
Submit metadata about a dataset with its object groups and data objects, derived from data sources or pipelines. 

Dataset Hierarchy:
- Dataset: Collection of one or more object groups
- Object Group: Related data objects of the same modality (e.g., all time series, all images)
- Data Object: Individual samples (one time series, one image, one document)

Requirements:
- Create a DataFrame for each object group where each row represents ONE data object
- Compute metadata per object (e.g., original_id, timestamps, dimensions)
- Convert DataFrames to Parquet format and wrap in FileInput objects
- Compute aggregated statistics for each group's modality_fields
- All files must be parquet format
- Provide chart descriptions for ALL object groups (chart visualizations are mandatory)

You must write code to populate a Python dictionary with dataset metadata named 'dataset_dict'. 
You must also create a 'files' variable containing a list of FileInput objects with the parquet data. 
FileInput objects must have: filename (str), file_data (bytes), content_type (str). 
The import path is: from project_server.client import FileInput
Again, all data should be output as dicts, except the list of files which is a list of FileInput objects! 

Chart Descriptions:
- You must provide a chart description for each object group in the dataset, matched by the name field
- Example: ChartDescription(group_name="forecast_series", description="Line chart showing past values in blue, forecast values in green, ground-truth values in orange, and the forecast start point in a vertical line.")

IMPORTANT: If a target entity ID is provided in the prompt, you MUST include 'dataset_id' in the dictionary with that UUID value.
When 'dataset_id' is present, you should add object groups to that existing dataset (not create a new dataset).
Otherwise, create a new dataset with full metadata (without dataset_id field). 

No hallucinations! Use code to extract the dataset metadata, don't make it up. 

The schema the dataset_dict must abide by is:
{json.dumps(DatasetCreate.model_json_schema())}

The schema each data object row of the data objects file dataframe must abide by is:
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

    if "dataset_dict" not in python_code:
        raise ModelRetry(
            "The output data dictionary to submit must be named 'dataset_dict'!")

    if "files" not in python_code:
        raise ModelRetry(
            "The 'files' variable must be created in the code to submit the dataset!")

    try:
        python_code = remove_print_statements_from_code(python_code)
        submission_code = (
            f"{python_code}\n"
            "import asyncio\n"
            "from project_server.client import ProjectClient\n"
            "from project_server.client.requests.data_objects import post_dataset, post_object_group, get_dataset\n"
            "from project_server.client.requests.project import post_add_entity\n"
            "from synesis_schemas.main_server import DatasetCreate, DataObjectGroupCreate, AddEntityToProject\n"
            "from uuid import UUID\n"
            "import json\n"
            "\n"
            "async def run_submission():\n"
            f"    client = ProjectClient(bearer_token='{ctx.deps.bearer_token}')\n"
            "    # The agent should have prepared 'files' list with FileInput objects\n"
            "    if 'files' not in locals() and 'files' not in globals():\n"
            "        raise ValueError('files variable not found. The agent must create FileInput objects for dataframes in all groups.')\n"
            "    \n"
            "    # Check if this is adding to an existing dataset or creating a new one\n"
            "    if 'dataset_id' in dataset_dict:\n"
            "        # Add object groups to existing dataset\n"
            "        dataset_id = UUID(dataset_dict['dataset_id'])\n"
            "        groups_data = dataset_dict.get('groups', [])\n"
            "        \n"
            "        # Add each object group\n"
            "        for group_dict in groups_data:\n"
            "            group_create = DataObjectGroupCreate(**group_dict)\n"
            "            # Filter files for this group based on the group's objects_files\n"
            "            group_files = [f for f in files if any(of['filename'] == f.filename for of in group_dict.get('objects_files', []))]\n"
            "            await post_object_group(client, dataset_id, group_create, group_files)\n"
            "        \n"
            "        # Get updated dataset\n"
            "        result = await get_dataset(client, dataset_id)\n"
            "    else:\n"
            "        # Create new dataset\n"
            "        dataset_create_obj = DatasetCreate(**dataset_dict)\n"
            "        result = await post_dataset(client, files, dataset_create_obj)\n"
            "        # Add dataset to project\n"
            "        add_entity_request = AddEntityToProject(\n"
            f"            project_id=UUID('{ctx.deps.project.id}'),\n"
            "            entity_type='dataset',\n"
            "            entity_id=result.id\n"
            "        )\n"
            "        await post_add_entity(client, add_entity_request)\n"
            "    print(json.dumps(result.model_dump(), default=str))\n"
            "\n"
            "asyncio.run(run_submission())"
        )
        out, err = await run_python_code_in_container(submission_code, ctx.deps.container_name)

        logger.info("DATASET SUBMISSION CODE:")
        logger.info(submission_code)
        logger.info("DATASET SUBMISSION CODE END")
        logger.info("DATASET SUBMISSION OUTPUT:")
        logger.info(out)
        logger.info("DATASET SUBMISSION OUTPUT END")

        if err:
            logger.info(f"Code execution error: {err}")
            raise ValueError(f"Code execution error: {err}")

        result_data = json.loads(out.strip())
        result_obj = Dataset(**result_data)

        # Create mapping of group names to chart descriptions
        chart_desc_map = {
            cd.group_name: cd.description for cd in chart_descriptions}

        # Verify we have chart descriptions for all object groups
        missing_charts = [
            g.name for g in result_obj.object_groups if g.name not in chart_desc_map]
        if missing_charts:
            logger.info(
                f"Missing chart descriptions for object groups: {', '.join(missing_charts)}. ")
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


dataset_agent = Agent[HelperDeps, str](
    model=get_model(),
    deps_type=HelperDeps,
    system_prompt=dataset_system_prompt,
    retries=3,
    output_type=submit_dataset
)


pipeline_system_prompt = """
Submit metadata about a data processing or machine learning pipeline. 

IMPORTANT: If a target entity ID is provided in the prompt, you MUST set pipeline_id to that UUID in the PipelineImplementationCreate object.
When pipeline_id is set, you are adding an implementation to an existing pipeline (do not include pipeline_create).
Otherwise, if this is a brand new pipeline entity, you must include the pipeline_create object (and leave pipeline_id as None).
"""


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
    try:
        pipeline_implementation = await post_pipeline_implementation(ctx.deps.client, pipeline_implementation_create)
        out_str = f"Pipeline implementation created: {pipeline_implementation.model_dump_json(indent=4)}\n\n"
        for run in runs:
            run.pipeline_id = pipeline_implementation.id
            pipe_run_obj = await post_pipeline_run(ctx.deps.client, run)
            out_str += f"Pipeline run created: {pipe_run_obj.model_dump_json(indent=4)}\n\n"

        if pipeline_implementation_create.pipeline_create:
            await post_add_entity(ctx.deps.client, AddEntityToProject(
                project_id=ctx.deps.project.id,
                entity_type="pipeline",
                entity_id=pipeline_implementation.id
            ))

        return out_str
    except Exception as e:
        raise ModelRetry(f"Failed to submit pipeline implementation: {str(e)}")


pipeline_agent = Agent[HelperDeps, str](
    model=get_model(),
    deps_type=HelperDeps,
    system_prompt=pipeline_system_prompt,
    retries=3,
    output_type=submit_pipeline_implementation
)


model_entity_system_prompt = """
Submit metadata about a model, which can be a machine learning model, a rule-based model, an optimization model, etc. 

IMPORTANT: If a target entity ID is provided in the prompt, you MUST set model_entity_id to that UUID in the ModelEntityImplementationCreate object.
When model_entity_id is set, you are adding an implementation to an existing model entity (do not include model_entity_create).
Otherwise, if this is a brand new model entity, you must include the model_entity_create object (and leave model_entity_id as None).
"""


async def submit_model_entity_implementation(ctx: RunContext[HelperDeps], model_entity_implementation_create: ModelEntityImplementationCreate) -> str:
    try:
        model_entity_obj = await post_model_entity_implementation(ctx.deps.client, model_entity_implementation_create)
        if model_entity_implementation_create.model_entity_create:
            await post_add_entity(ctx.deps.client, AddEntityToProject(
                project_id=ctx.deps.project.id,
                entity_type="model_entity",
                entity_id=model_entity_obj.id
            ))
        return model_entity_obj.model_dump_json(indent=4)
    except Exception as e:
        raise ModelRetry(f"Failed to submit model entity: {str(e)}")


model_entity_agent = Agent[HelperDeps, str](
    model=get_model(),
    deps_type=HelperDeps,
    system_prompt=model_entity_system_prompt,
    retries=3,
    output_type=submit_model_entity_implementation
)

#


async def _create_chart_for_object_group(
    ctx: RunContext[HelperDeps],
    object_group_id: uuid.UUID,
    chart_description: str,
    datasets_to_inject: List[uuid.UUID],
    data_sources_to_inject: List[uuid.UUID],
) -> ChartAgentOutput:

    try:
        object_group = await get_object_group(ctx.deps.client, object_group_id)
    except Exception as e:
        raise ModelRetry(
            f"Failed to get object group. The ID must be the DB UUID of the group: {str(e)}")

    chart_result = await chart_agent.run(
        chart_description,
        deps=ChartDeps(
            container_name=ctx.deps.container_name,
            client=ctx.deps.client,
            project_id=ctx.deps.project.id,
            datasets_injected=datasets_to_inject,
            data_sources_injected=data_sources_to_inject,
            object_group=object_group
        )
    )
    save_path = AGENT_OUTPUTS_INTERNAL_DIR / f"{object_group_id}.py"
    await write_file_to_container(save_path, chart_result.output.script_content, ctx.deps.container_name)
    await create_object_group_echart(
        ctx.deps.client,
        object_group_id,
        ObjectGroupEChartCreate(chart_script_path=str(save_path)))

    return chart_result.output
