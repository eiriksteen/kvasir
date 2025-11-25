import io
from uuid import UUID
from pathlib import Path
from typing import List, Union, Tuple

from kvasir_ontology.entities.data_source.data_model import DataSourceCreate, DataSource
from kvasir_ontology.entities.data_source.interface import DataSourceInterface
from kvasir_ontology.entities.analysis.data_model import AnalysisCreate, Analysis
from kvasir_ontology.entities.analysis.interface import AnalysisInterface
from kvasir_ontology.entities.dataset.data_model import DatasetCreate, Dataset
from kvasir_ontology.entities.dataset.interface import DatasetInterface
from kvasir_ontology.entities.pipeline.data_model import PipelineCreate, Pipeline
from kvasir_ontology.entities.pipeline.interface import PipelineInterface
from kvasir_ontology.entities.model.data_model import ModelInstantiatedCreate, ModelInstantiated
from kvasir_ontology.entities.model.interface import ModelInterface
from kvasir_ontology.visualization.interface import VisualizationInterface
from kvasir_ontology.graph.interface import GraphInterface
from kvasir_ontology.graph.data_model import EdgeDefinition, EntityNodeCreate, EntityGraph, get_entity_graph_description, NODE_TYPE_LITERAL
from kvasir_ontology.code.interface import CodeInterface
from kvasir_ontology._description_utils import (
    get_data_source_description,
    get_dataset_description,
    get_pipeline_description,
    get_pipeline_run_description,
    get_model_entity_description,
    get_analysis_description
)


class Ontology:

    def __init__(
            self,
            user_id: UUID,
            mount_group_id: UUID,
            data_source_interface: DataSourceInterface,
            analysis_interface: AnalysisInterface,
            dataset_interface: DatasetInterface,
            pipeline_interface: PipelineInterface,
            model_interface: ModelInterface,
            visualization_interface: VisualizationInterface,
            graph_interface: GraphInterface,
            code_interface: CodeInterface
    ) -> None:

        self.user_id = user_id
        self.mount_group_id = mount_group_id
        self.data_sources = data_source_interface
        self.analyses = analysis_interface
        self.datasets = dataset_interface
        self.pipelines = pipeline_interface
        self.models = model_interface
        self.visualizations = visualization_interface
        self.graph = graph_interface
        self.code = code_interface

    async def get_entity_graph(self) -> EntityGraph:
        return await self.graph.get_entity_graph(root_group_id=self.mount_group_id)

    async def get_entities(self, entity_ids: List[UUID]) -> List[Union[DataSource, Dataset, Pipeline, ModelInstantiated, Analysis]]:
        data_sources = await self.data_sources.get_data_sources(entity_ids)
        datasets = await self.datasets.get_datasets(entity_ids)
        pipelines = await self.pipelines.get_pipelines(entity_ids)
        models_instantiated = await self.models.get_models_instantiated(entity_ids)
        analyses = await self.analyses.get_analyses(entity_ids)
        return data_sources + datasets + pipelines + models_instantiated + analyses

    async def describe_entity(self, entity_id: UUID, entity_type: NODE_TYPE_LITERAL, include_connections: bool = True) -> str:
        if entity_type == "data_source":
            return await get_data_source_description(entity_id, self, include_connections=include_connections)

        if entity_type == "dataset":
            return await get_dataset_description(entity_id, self, include_connections=include_connections)

        if entity_type == "pipeline":
            return await get_pipeline_description(entity_id, self, include_connections=include_connections)

        if entity_type == "model_instantiated":
            return await get_model_entity_description(entity_id, self, include_connections=include_connections)

        if entity_type == "analysis":
            return await get_analysis_description(entity_id, self, include_connections=include_connections)

        if entity_type == "pipeline_run":
            return await get_pipeline_run_description(
                entity_id, self,
                show_pipeline_description=True,
                include_connections=include_connections
            )

    async def describe_mount_group(self, include_positions: bool = False) -> str:
        mount_group = await self.graph.get_node_group(self.mount_group_id)
        if not mount_group:
            raise RuntimeError(
                f"No mount group found for ID: {self.mount_group_id}")

        entity_graph = await self.get_entity_graph()
        entity_graph_description = get_entity_graph_description(
            entity_graph, include_positions=include_positions)

        desc = (
            f"<mount_group id=\"{self.mount_group_id}\" name=\"{mount_group.name}\" description=\"{mount_group.description}\" python_package_name=\"{mount_group.python_package_name}\">\n\n" +
            f"<entity_graph>\n\n{entity_graph_description}\n\n</entity_graph>" +
            "\n\n</mount_group>"
        )
        return desc

    async def describe_entities(self, entity_ids: List[UUID], include_connections: bool = True) -> str:
        if not entity_ids:
            return ""

        entity_graph = await self.get_entity_graph()

        id_to_type: dict[UUID, NODE_TYPE_LITERAL] = {}
        for entity in entity_graph.data_sources:
            id_to_type[entity.id] = "data_source"
        for entity in entity_graph.datasets:
            id_to_type[entity.id] = "dataset"
        for entity in entity_graph.analyses:
            id_to_type[entity.id] = "analysis"
        for entity in entity_graph.pipelines:
            id_to_type[entity.id] = "pipeline"
        for entity in entity_graph.models_instantiated:
            id_to_type[entity.id] = "model_instantiated"

        entity_descriptions = []
        for entity_id in entity_ids:
            if entity_id in id_to_type:
                entity_type = id_to_type[entity_id]
                description = await self.describe_entity(entity_id, entity_type, include_connections)
                entity_descriptions.append(description)

        final_out = (
            "<entity_descriptions>\n\n" +
            "\n\n".join(entity_descriptions) +
            "\n\n</entity_descriptions>"
        )

        return final_out

    async def insert_data_source(
        self,
        data_source: DataSourceCreate,
        edges: List[EdgeDefinition],
        x_position: float = 400,
        y_position: float = 400,
    ) -> DataSource:

        data_source_obj = await self.data_sources.create_data_source(data_source)
        await self.graph.add_node(EntityNodeCreate(
            id=data_source_obj.id,
            name=data_source_obj.name,
            entity_type="data_source",
            node_groups=[self.mount_group_id],
            x_position=x_position,
            y_position=y_position,
        ))
        await self.graph.create_edges(edges)

        return data_source_obj

    async def insert_dataset(
        self,
        dataset: DatasetCreate,
        edges: List[EdgeDefinition],
        x_position: float = 500,
        y_position: float = 400,
    ) -> Dataset:

        dataset_obj = await self.datasets.create_dataset(dataset)
        await self.graph.add_node(EntityNodeCreate(
            id=dataset_obj.id,
            name=dataset_obj.name,
            entity_type="dataset",
            node_groups=[self.mount_group_id],
            x_position=x_position,
            y_position=y_position,
        ))
        await self.graph.create_edges(edges)

        return dataset_obj

    async def insert_analysis(
        self,
        analysis: AnalysisCreate,
        edges: List[EdgeDefinition],
        x_position: float = 600,
        y_position: float = 400,
    ) -> Analysis:

        analysis_obj = await self.analyses.create_analysis(analysis)
        await self.graph.add_node(EntityNodeCreate(
            id=analysis_obj.id,
            name=analysis_obj.name,
            entity_type="analysis",
            node_groups=[self.mount_group_id],
            x_position=x_position,
            y_position=y_position,
        ))
        await self.graph.create_edges(edges)

        return analysis_obj

    async def insert_pipeline(
        self,
        pipeline: PipelineCreate,
        edges: List[EdgeDefinition],
        x_position: float = 700,
        y_position: float = 400,
    ) -> Pipeline:

        pipeline_obj = await self.pipelines.create_pipeline(pipeline)
        await self.graph.add_node(EntityNodeCreate(
            id=pipeline_obj.id,
            name=pipeline_obj.name,
            entity_type="pipeline",
            node_groups=[self.mount_group_id],
            x_position=x_position,
            y_position=y_position,
        ))
        await self.graph.create_edges(edges)

        return pipeline_obj

    async def insert_model_instantiated(
        self,
        model_instantiated: ModelInstantiatedCreate,
        edges: List[EdgeDefinition],
        x_position: float = 800,
        y_position: float = 400,
    ) -> ModelInstantiated:

        model_instantiated_obj = await self.models.create_model_instantiated(model_instantiated)
        await self.graph.add_node(EntityNodeCreate(
            id=model_instantiated_obj.id,
            name=model_instantiated_obj.name,
            entity_type="model_instantiated",
            node_groups=[self.mount_group_id],
            x_position=x_position,
            y_position=y_position,
        ))
        await self.graph.create_edges(edges)

        return model_instantiated_obj

    async def delete_data_source(self, data_source_id: UUID) -> None:

        all_edges = await self.graph.get_node_edges(data_source_id)
        if all_edges:
            await self.graph.remove_edges(all_edges)
        node_groups = await self.graph.get_node_groups(data_source_id)
        if node_groups:
            await self.graph.remove_nodes_from_groups([data_source_id], [group.id for group in node_groups])
        await self.graph.delete_node(data_source_id)
        await self.data_sources.delete_data_source(data_source_id)

    async def delete_dataset(self, dataset_id: UUID) -> None:

        all_edges = await self.graph.get_node_edges(dataset_id)
        if all_edges:
            await self.graph.remove_edges(all_edges)
        node_groups = await self.graph.get_node_groups(dataset_id)
        if node_groups:
            await self.graph.remove_nodes_from_groups([dataset_id], [group.id for group in node_groups])
        await self.graph.delete_node(dataset_id)
        await self.datasets.delete_dataset(dataset_id)

    async def delete_analysis(self, analysis_id: UUID) -> None:

        all_edges = await self.graph.get_node_edges(analysis_id)
        if all_edges:
            await self.graph.remove_edges(all_edges)
        node_groups = await self.graph.get_node_groups(analysis_id)
        if node_groups:
            await self.graph.remove_nodes_from_groups([analysis_id], [group.id for group in node_groups])
        await self.graph.delete_node(analysis_id)
        await self.analyses.delete_analysis(analysis_id)

    async def delete_pipeline(self, pipeline_id: UUID) -> None:
        pipeline_runs = await self.pipelines.get_pipeline_runs(pipeline_ids=[pipeline_id])
        pipeline_run_ids = [run.id for run in pipeline_runs]

        if pipeline_run_ids:
            await self.graph.remove_pipeline_run_edges(pipeline_run_ids)

        all_edges = await self.graph.get_node_edges(pipeline_id)
        if all_edges:
            await self.graph.remove_edges(all_edges)
        node_groups = await self.graph.get_node_groups(pipeline_id)
        if node_groups:
            await self.graph.remove_nodes_from_groups([pipeline_id], [group.id for group in node_groups])
        await self.graph.delete_node(pipeline_id)
        await self.pipelines.delete_pipeline(pipeline_id)

    async def delete_model_instantiated(self, model_instantiated_id: UUID) -> None:

        all_edges = await self.graph.get_node_edges(model_instantiated_id)
        if all_edges:
            await self.graph.remove_edges(all_edges)
        node_groups = await self.graph.get_node_groups(model_instantiated_id)
        if node_groups:
            await self.graph.remove_nodes_from_groups([model_instantiated_id], [group.id for group in node_groups])
        await self.graph.delete_node(model_instantiated_id)
        await self.models.delete_model_instantiated(model_instantiated_id)

    async def get_mounted_data_sources(self) -> List[DataSource]:
        entity_graph = await self.get_entity_graph()
        data_source_ids = [ds.id for ds in entity_graph.data_sources]
        if not data_source_ids:
            return []
        return await self.data_sources.get_data_sources(data_source_ids)

    async def get_mounted_datasets(self) -> List[Dataset]:
        entity_graph = await self.get_entity_graph()
        dataset_ids = [d.id for d in entity_graph.datasets]
        if not dataset_ids:
            return []
        return await self.datasets.get_datasets(dataset_ids)

    async def get_mounted_pipelines(self) -> List[Pipeline]:
        entity_graph = await self.get_entity_graph()
        pipeline_ids = [p.id for p in entity_graph.pipelines]
        if not pipeline_ids:
            return []
        return await self.pipelines.get_pipelines(pipeline_ids)

    async def get_mounted_models_instantiated(self) -> List[ModelInstantiated]:
        entity_graph = await self.get_entity_graph()
        model_ids = [m.id for m in entity_graph.models_instantiated]
        if not model_ids:
            return []
        return await self.models.get_models_instantiated(model_ids)

    async def get_mounted_analyses(self) -> List[Analysis]:
        entity_graph = await self.get_entity_graph()
        analysis_ids = [a.id for a in entity_graph.analyses]
        if not analysis_ids:
            return []
        return await self.analyses.get_analyses(analysis_ids)

    async def insert_files_data_sources(self, file_bytes: List[io.BytesIO], file_names: List[str], edges: List[EdgeDefinition]) -> Tuple[List[DataSource], List[Path]]:
        file_objs, file_paths = await self.data_sources.create_files_data_sources(file_bytes, file_names, self.mount_group_id)
        await self.graph.add_nodes(
            [EntityNodeCreate(
                id=file_obj.id,
                name=file_obj.name,
                entity_type="data_source",
                node_groups=[self.mount_group_id],
                x_position=400,
                y_position=400,
            ) for file_obj in file_objs]
        )
        await self.graph.create_edges(edges)
        return file_objs, file_paths

    async def describe_analysis(self, analysis_obj: Analysis, include_connections: bool = True) -> str:
        return await get_analysis_description(analysis_obj.id, self, include_connections=include_connections)
