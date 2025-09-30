import uuid
from typing import List

from project_server.app_secrets import MODEL_WEIGHTS_DIR
from project_server.entity_manager import LocalDatasetManager, DatasetWithRawData, ObjectGroupCreateWithRawData, VariableGroupCreateWithRawData, DatasetCreateWithRawData
from synesis_schemas.main_server import PipelineOutputMapping, PipelineInputMapping, DatasetSources


class PipelineManager:

    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.dataset_manager = LocalDatasetManager(self.bearer_token)

    async def load_pipeline_inputs(
            self,
            input_dataset_ids: List[uuid.UUID],
            input_mapping: PipelineInputMapping
    ) -> dict:

        datasets: List[DatasetWithRawData] = [
            await self.dataset_manager.get_dataset_with_raw_data(dataset_id) for dataset_id in input_dataset_ids
        ]
        out = {}

        for object_group_mapping in input_mapping.from_dataset_object_groups:
            dataset = next(ds for ds in datasets if ds.name ==
                           object_group_mapping.dataset_name)
            object_group = next(og for og in dataset.object_groups if og.name ==
                                object_group_mapping.dataset_object_group_name)
            out[object_group_mapping.pipeline_input_variable_name] = object_group.data

        for model_entity_mapping in input_mapping.from_model_entities:
            if model_entity_mapping.model_entity_weights_dir_name is None:
                weights_save_dir = MODEL_WEIGHTS_DIR / f"{uuid.uuid4()}"
            else:
                weights_save_dir = model_entity_mapping.model_entity_weights_dir_name

            out[model_entity_mapping.pipeline_input_weights_dir_variable_name] = weights_save_dir

        return out

    async def save_pipeline_outputs(
            self,
            pipeline_id: uuid.UUID,
            dataset_name: str,
            dataset_description: str,
            pipeline_output: dict,
            output_mapping: PipelineOutputMapping
    ) -> str:

        object_group_creates: List[ObjectGroupCreateWithRawData] = []
        variable_group_creates: List[VariableGroupCreateWithRawData] = []

        for output_object_group_mapping in output_mapping.output_object_groups:
            object_group_creates.append(
                ObjectGroupCreateWithRawData(
                    **output_object_group_mapping.output_create.model_dump(),
                    data=pipeline_output[output_object_group_mapping.output_object_group_variable_name]
                )
            )

        for output_variable_group_mapping in output_mapping.output_variable_groups:
            variable_group_creates.append(
                VariableGroupCreateWithRawData(
                    **output_variable_group_mapping.output_create.model_dump(),
                    data=pipeline_output[output_variable_group_mapping.output_variable_group_variable_name]
                )
            )

        dataset_create = DatasetCreateWithRawData(
            name=dataset_name,
            description=dataset_description,
            object_groups=object_group_creates,
            variable_groups=variable_group_creates
        )

        out = await self.dataset_manager.upload_dataset(
            dataset_create,
            DatasetSources(pipeline_ids=[pipeline_id]),
            output_json=True
        )

        return out
