import uuid
from typing import List, Union, Dict
from dataclasses import dataclass
from pathlib import Path


from project_server.app_secrets import MODEL_WEIGHTS_DIR
from project_server.entity_manager import (
    LocalDatasetManager,
    ObjectGroupCreateWithRawData,
    VariableGroupCreateWithRawData,
    DatasetCreateWithRawData,
    ObjectGroupWithRawData,
)
from synesis_schemas.main_server import (
    DatasetSources,
    GetModelEntityByIDsRequest,
    PipelineOutputObjectGroupDefinitionCreate,
    PipelineOutputObjectGroupDefinitionInDB,
    ObjectGroupInPipelineCreate,
    ObjectGroupInPipelineInDB,
    ModelEntityInPipelineCreate,
    ModelEntityInPipelineInDB,
)
from project_server.client import get_model_entities_by_ids, get_user_pipeline
from project_server.client import ProjectClient, get_model_entities_by_ids
from synesis_data_structures.time_series.df_dataclasses import TimeSeriesStructure, TimeSeriesAggregationStructure


@dataclass
class ObjectGroupInput:
    input_variable_name: str
    data: Union[TimeSeriesStructure, TimeSeriesAggregationStructure]


@dataclass
class ModelInput:
    input_variable_name: str
    config: dict


@dataclass
class PipelineInputs:
    args_dict: dict
    object_group_inputs: List[ObjectGroupInput]
    model_inputs: List[ModelInput]


class PipelineManager:

    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.client = ProjectClient(self.bearer_token)
        self.dataset_manager = LocalDatasetManager(self.bearer_token)

    async def load_pipeline_inputs(
        self,
        pipeline_id: uuid.UUID,
        input_object_groups: List[Union[ObjectGroupInPipelineCreate, ObjectGroupInPipelineInDB]],
        input_model_entities: List[Union[ModelEntityInPipelineCreate,
                                         ModelEntityInPipelineInDB]],
        weights_save_dirs: Dict[uuid.UUID, str]
    ) -> dict:
        pipeline_obj = await get_user_pipeline(self.client, pipeline_id)

        input_object_group_ids = [
            o.object_group_id for o in input_object_groups]
        input_model_entity_ids = [
            m.model_entity_id for m in input_model_entities]

        model_entities = await get_model_entities_by_ids(self.client, GetModelEntityByIDsRequest(model_entity_ids=input_model_entity_ids))
        groups: List[ObjectGroupWithRawData] = [
            await self.dataset_manager.get_data_group_with_raw_data(group_id) for group_id in input_object_group_ids
        ]

        out_dict = {"function_args": pipeline_obj.args}

        for group in groups:
            variable_name = next(
                o.code_variable_name for o in input_object_groups if o.object_group_id == group.id)
            out_dict[variable_name] = group.data

        for model_entity in model_entities:
            if model_entity.id in weights_save_dirs:
                model_entity.config["weights_save_dir"] = Path(
                    weights_save_dirs[model_entity.id])
            elif model_entity.weights_save_dir is None:
                raise ValueError(
                    "No existing weights save dir found and no weights save dir provided")
            else:
                model_entity.config["weights_save_dir"] = Path(
                    model_entity.weights_save_dir)

            variable_name = next(
                m.code_variable_name for m in input_model_entities if m.model_entity_id == model_entity.id)
            out_dict[f"{variable_name}_config"] = model_entity.config

        return out_dict

    async def save_pipeline_dataset_output(
            self,
            pipeline_id: uuid.UUID,
            dataset_name: str,
            dataset_description: str,
            pipeline_output: object,
            output_object_group_definitions: List[Union[PipelineOutputObjectGroupDefinitionCreate, PipelineOutputObjectGroupDefinitionInDB]],
    ) -> str:

        assert hasattr(
            pipeline_output, "output_variables"), "Pipeline output must have an output_variables attribute"

        object_group_creates: List[ObjectGroupCreateWithRawData] = []
        for definition in output_object_group_definitions:
            assert hasattr(
                pipeline_output, definition.name), f"Pipeline output must have an {definition.name} attribute"
            object_group_creates.append(ObjectGroupCreateWithRawData(
                name=definition.name,
                entity_id_name=definition.output_entity_id_name,
                description=definition.description,
                structure_type=definition.structure_id,
                data=getattr(pipeline_output, definition.name)
            ))

        variable_group_create = VariableGroupCreateWithRawData(
            name=f"{dataset_name}_variables",
            description=f"{dataset_name} variables",
            data=getattr(pipeline_output, "output_variables")
        )

        dataset_create = DatasetCreateWithRawData(
            name=dataset_name,
            description=dataset_description,
            object_groups=object_group_creates,
            variable_groups=[variable_group_create]
        )

        out = await self.dataset_manager.upload_dataset(
            dataset_create,
            DatasetSources(pipeline_ids=[pipeline_id],
                           dataset_ids=[],
                           data_source_ids=[]),
            output_json=True
        )

        return out
