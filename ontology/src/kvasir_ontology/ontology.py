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
from kvasir_ontology.graph.data_model import EdgeCreate, LeafNodeCreate, EntityGraph, get_entity_graph_description, CHILD_TYPE_LITERAL, BranchNodeCreate
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
            mount_node_id: UUID,
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
        self.mount_node_id = mount_node_id
        self.data_sources = data_source_interface
        self.analyses = analysis_interface
        self.datasets = dataset_interface
        self.pipelines = pipeline_interface
        self.models = model_interface
        self.visualizations = visualization_interface
        self.graph = graph_interface
        self.code = code_interface

    async def get_entity_graph(self) -> EntityGraph:
        return await self.graph.get_entity_graph(self.mount_node_id)

    async def get_entities(self, entity_ids: List[UUID]) -> List[Union[DataSource, Dataset, Pipeline, ModelInstantiated, Analysis]]:
        data_sources = await self.data_sources.get_data_sources(entity_ids)
        datasets = await self.datasets.get_datasets(entity_ids)
        pipelines = await self.pipelines.get_pipelines(entity_ids)
        models_instantiated = await self.models.get_models_instantiated(entity_ids)
        analyses = await self.analyses.get_analyses(entity_ids)
        return data_sources + datasets + pipelines + models_instantiated + analyses

    async def describe_entity(self, entity_id: UUID, entity_type: CHILD_TYPE_LITERAL, include_connections: bool = True) -> str:
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

    async def describe_mount_node(self, include_positions: bool = False) -> str:
        mount_node = await self.graph.get_node(self.mount_node_id)
        if not mount_node:
            raise RuntimeError(
                f"No mount node found for ID: {self.mount_node_id}")

        entity_graph = await self.get_entity_graph()
        entity_graph_description = get_entity_graph_description(
            entity_graph, include_positions=include_positions)

        desc = (
            f"<mount_node id=\"{self.mount_node_id}\" name=\"{mount_node.name}\" description=\"{mount_node.description}\" python_package_name=\"{mount_node.python_package_name}\">\n\n" +
            f"<entity_graph>\n\n{entity_graph_description}\n\n</entity_graph>" +
            "\n\n</mount_node>"
        )
        return desc

    async def describe_entities(self, entity_ids: List[UUID], include_connections: bool = True) -> str:
        if not entity_ids:
            return ""

        entity_graph = await self.get_entity_graph()

        id_to_type: dict[UUID, CHILD_TYPE_LITERAL] = {}
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
        edges: List[EdgeCreate],
        x_position: float = 400,
        y_position: float = 400,
    ) -> DataSource:

        data_source_obj = await self.data_sources.create_data_source(data_source)
        await self.graph.add_nodes([LeafNodeCreate(
            entity_id=data_source_obj.id,
            name=data_source_obj.name,
            entity_type="data_source",
            parent_branch_nodes=[self.mount_node_id],
            x_position=x_position,
            y_position=y_position,
        )])
        await self.graph.create_edges(edges)

        return data_source_obj

    async def insert_data_source_group(
        self,
        name: str,
        description: str,
        data_sources: List[DataSourceCreate],
        edges: List[EdgeCreate],
        x_position: float = 400,
        y_position: float = 400
    ) -> List[DataSource]:
        data_source_objs = await self.data_sources.create_data_sources(data_sources)

        leaf_nodes = [
            LeafNodeCreate(
                entity_id=ds_obj.id,
                name=ds_obj.name,
                entity_type="data_source",
                x_position=x_position,
                y_position=y_position
            ) for ds_obj in data_source_objs
        ]

        branch_node = BranchNodeCreate(
            name=name,
            x_position=x_position,
            y_position=y_position,
            description=description,
            children=leaf_nodes,
            parent_branch_nodes=[self.mount_node_id]
        )

        await self.graph.add_nodes([branch_node])
        await self.graph.create_edges(edges)
        return data_source_objs

    async def insert_dataset(
        self,
        dataset: DatasetCreate,
        edges: List[EdgeCreate],
        x_position: float = 500,
        y_position: float = 400,
    ) -> Dataset:

        dataset_obj = await self.datasets.create_dataset(dataset)
        await self.graph.add_nodes([LeafNodeCreate(
            entity_id=dataset_obj.id,
            name=dataset_obj.name,
            entity_type="dataset",
            parent_branch_nodes=[self.mount_node_id],
            x_position=x_position,
            y_position=y_position,
        )])
        await self.graph.create_edges(edges)

        return dataset_obj

    async def insert_dataset_group(
        self,
        name: str,
        description: str,
        datasets: List[DatasetCreate],
        edges: List[EdgeCreate],
        x_position: float = 500,
        y_position: float = 400
    ) -> List[Dataset]:
        dataset_objs: List[Dataset] = []
        for dataset in datasets:
            dataset_obj = await self.datasets.create_dataset(dataset)
            dataset_objs.append(dataset_obj)

        leaf_nodes = [
            LeafNodeCreate(
                entity_id=ds_obj.id,
                name=ds_obj.name,
                entity_type="dataset",
                x_position=x_position,
                y_position=y_position
            ) for ds_obj in dataset_objs
        ]

        branch_node = BranchNodeCreate(
            name=name,
            x_position=x_position,
            y_position=y_position,
            description=description,
            children=leaf_nodes,
            parent_branch_nodes=[self.mount_node_id]
        )

        await self.graph.add_nodes([branch_node])
        await self.graph.create_edges(edges)
        return dataset_objs

    async def insert_analysis(
        self,
        analysis: AnalysisCreate,
        edges: List[EdgeCreate],
        x_position: float = 600,
        y_position: float = 400,
    ) -> Analysis:

        analysis_obj = await self.analyses.create_analysis(analysis)
        await self.graph.add_nodes([LeafNodeCreate(
            entity_id=analysis_obj.id,
            name=analysis_obj.name,
            entity_type="analysis",
            parent_branch_nodes=[self.mount_node_id],
            x_position=x_position,
            y_position=y_position,
        )])
        await self.graph.create_edges(edges)

        return analysis_obj

    async def insert_analysis_group(
        self,
        name: str,
        description: str,
        analyses: List[AnalysisCreate],
        edges: List[EdgeCreate],
        x_position: float = 600,
        y_position: float = 400
    ) -> List[Analysis]:
        analysis_objs: List[Analysis] = []
        for analysis in analyses:
            analysis_obj = await self.analyses.create_analysis(analysis)
            analysis_objs.append(analysis_obj)

        leaf_nodes = [
            LeafNodeCreate(
                entity_id=analysis_obj.id,
                name=analysis_obj.name,
                entity_type="analysis",
                x_position=x_position,
                y_position=y_position
            ) for analysis_obj in analysis_objs
        ]

        branch_node = BranchNodeCreate(
            name=name,
            x_position=x_position,
            y_position=y_position,
            description=description,
            children=leaf_nodes,
            parent_branch_nodes=[self.mount_node_id]
        )

        await self.graph.add_nodes([branch_node])
        await self.graph.create_edges(edges)
        return analysis_objs

    async def insert_pipeline(
        self,
        pipeline: PipelineCreate,
        edges: List[EdgeCreate],
        x_position: float = 700,
        y_position: float = 400,
    ) -> Pipeline:

        pipeline_obj = await self.pipelines.create_pipeline(pipeline)
        await self.graph.add_nodes([LeafNodeCreate(
            entity_id=pipeline_obj.id,
            name=pipeline_obj.name,
            entity_type="pipeline",
            parent_branch_nodes=[self.mount_node_id],
            x_position=x_position,
            y_position=y_position,
        )])
        await self.graph.create_edges(edges)

        return pipeline_obj

    async def insert_pipeline_group(
        self,
        name: str,
        description: str,
        pipelines: List[PipelineCreate],
        edges: List[EdgeCreate],
        x_position: float = 700,
        y_position: float = 400
    ) -> List[Pipeline]:
        pipeline_objs: List[Pipeline] = []
        for pipeline in pipelines:
            pipeline_obj = await self.pipelines.create_pipeline(pipeline)
            pipeline_objs.append(pipeline_obj)

        leaf_nodes = [
            LeafNodeCreate(
                entity_id=pipeline_obj.id,
                name=pipeline_obj.name,
                entity_type="pipeline",
                x_position=x_position,
                y_position=y_position
            ) for pipeline_obj in pipeline_objs
        ]

        branch_node = BranchNodeCreate(
            name=name,
            x_position=x_position,
            y_position=y_position,
            description=description,
            children=leaf_nodes,
            parent_branch_nodes=[self.mount_node_id]
        )

        await self.graph.add_nodes([branch_node])
        await self.graph.create_edges(edges)
        return pipeline_objs

    async def insert_model_instantiated(
        self,
        model_instantiated: ModelInstantiatedCreate,
        edges: List[EdgeCreate],
        x_position: float = 800,
        y_position: float = 400,
    ) -> ModelInstantiated:

        model_instantiated_obj = await self.models.create_model_instantiated(model_instantiated)
        await self.graph.add_nodes([LeafNodeCreate(
            entity_id=model_instantiated_obj.id,
            name=model_instantiated_obj.name,
            entity_type="model_instantiated",
            parent_branch_nodes=[self.mount_node_id],
            x_position=x_position,
            y_position=y_position,
        )])
        await self.graph.create_edges(edges)

        return model_instantiated_obj

    async def insert_model_instantiated_group(
        self,
        name: str,
        description: str,
        models_instantiated: List[ModelInstantiatedCreate],
        edges: List[EdgeCreate],
        x_position: float = 800,
        y_position: float = 400
    ) -> List[ModelInstantiated]:
        model_instantiated_objs: List[ModelInstantiated] = []
        for model_instantiated in models_instantiated:
            model_instantiated_obj = await self.models.create_model_instantiated(model_instantiated)
            model_instantiated_objs.append(model_instantiated_obj)

        leaf_nodes = [
            LeafNodeCreate(
                entity_id=model_obj.id,
                name=model_obj.name,
                entity_type="model_instantiated",
                x_position=x_position,
                y_position=y_position
            ) for model_obj in model_instantiated_objs
        ]

        branch_node = BranchNodeCreate(
            name=name,
            x_position=x_position,
            y_position=y_position,
            description=description,
            children=leaf_nodes,
            parent_branch_nodes=[self.mount_node_id]
        )

        await self.graph.add_nodes([branch_node])
        await self.graph.create_edges(edges)
        return model_instantiated_objs

    async def delete_data_source(self, data_source_id: UUID) -> None:
        await self.graph.delete_nodes(entity_ids=[data_source_id])
        await self.data_sources.delete_data_source(data_source_id)

    async def delete_dataset(self, dataset_id: UUID) -> None:
        await self.graph.delete_nodes(entity_ids=[dataset_id])
        await self.datasets.delete_dataset(dataset_id)

    async def delete_analysis(self, analysis_id: UUID) -> None:
        await self.graph.delete_nodes(entity_ids=[analysis_id])
        await self.analyses.delete_analysis(analysis_id)

    async def delete_pipeline(self, pipeline_id: UUID) -> None:
        await self.graph.delete_nodes(entity_ids=[pipeline_id])
        await self.pipelines.delete_pipeline(pipeline_id)

    async def delete_model_instantiated(self, model_instantiated_id: UUID) -> None:
        await self.graph.delete_nodes(entity_ids=[model_instantiated_id])
        await self.models.delete_model_instantiated(model_instantiated_id)

    async def delete_entity_branch(self, node_id: UUID) -> None:
        node = await self.graph.get_node(node_id)

        if node.node_type == "leaf":
            entity_id = node.entity_id
            entity_type = node.entity_type

            if entity_type == "data_source":
                await self.delete_data_source(entity_id)
            elif entity_type == "dataset":
                await self.delete_dataset(entity_id)
            elif entity_type == "analysis":
                await self.delete_analysis(entity_id)
            elif entity_type == "pipeline":
                await self.delete_pipeline(entity_id)
            elif entity_type == "model_instantiated":
                await self.delete_model_instantiated(entity_id)
            else:
                await self.graph.delete_nodes(node_ids=[node_id])
        else:
            leaf_nodes = await self.graph.get_node_leaves(node_id)

            entities_by_type = {
                "data_source": [],
                "dataset": [],
                "analysis": [],
                "pipeline": [],
                "model_instantiated": []
            }

            all_entity_ids = []
            for leaf in leaf_nodes:
                if leaf.entity_type in entities_by_type:
                    entities_by_type[leaf.entity_type].append(leaf.entity_id)
                    all_entity_ids.append(leaf.entity_id)

            if all_entity_ids:
                await self.graph.delete_nodes(entity_ids=all_entity_ids)

                for entity_id in entities_by_type["data_source"]:
                    await self.data_sources.delete_data_source(entity_id)

                for entity_id in entities_by_type["dataset"]:
                    await self.datasets.delete_dataset(entity_id)

                for entity_id in entities_by_type["analysis"]:
                    await self.analyses.delete_analysis(entity_id)

                for entity_id in entities_by_type["pipeline"]:
                    await self.pipelines.delete_pipeline(entity_id)

                for entity_id in entities_by_type["model_instantiated"]:
                    await self.models.delete_model_instantiated(entity_id)

            await self.graph.delete_nodes(node_ids=[node_id])

    async def get_mounted_data_sources(self) -> List[DataSource]:
        leaves = await self.graph.get_node_leaves(self.mount_node_id)
        data_source_ids = [
            leaf.entity_id for leaf in leaves if leaf.entity_type == "data_source"]
        if not data_source_ids:
            return []
        response = await self.data_sources.get_data_sources(data_source_ids)
        return response

    async def get_mounted_datasets(self) -> List[Dataset]:
        leaves = await self.graph.get_node_leaves(self.mount_node_id)
        dataset_ids = [
            leaf.entity_id for leaf in leaves if leaf.entity_type == "dataset"]
        if not dataset_ids:
            return []
        return await self.datasets.get_datasets(dataset_ids)

    async def get_mounted_pipelines(self) -> List[Pipeline]:
        leaves = await self.graph.get_node_leaves(self.mount_node_id)
        pipeline_ids = [
            leaf.entity_id for leaf in leaves if leaf.entity_type == "pipeline"]
        if not pipeline_ids:
            return []
        return await self.pipelines.get_pipelines(pipeline_ids)

    async def get_mounted_models_instantiated(self) -> List[ModelInstantiated]:
        leaves = await self.graph.get_node_leaves(self.mount_node_id)
        model_ids = [
            leaf.entity_id for leaf in leaves if leaf.entity_type == "model_instantiated"]
        if not model_ids:
            return []
        return await self.models.get_models_instantiated(model_ids)

    async def get_mounted_analyses(self) -> List[Analysis]:
        leaves = await self.graph.get_node_leaves(self.mount_node_id)
        analysis_ids = [
            leaf.entity_id for leaf in leaves if leaf.entity_type == "analysis"]
        if not analysis_ids:
            return []
        return await self.analyses.get_analyses(analysis_ids)

    async def insert_files_data_sources(self, file_bytes: List[io.BytesIO], file_names: List[str], edges: List[EdgeCreate]) -> Tuple[List[DataSource], List[Path]]:
        file_objs, file_paths = await self.data_sources.create_files_data_sources(file_bytes, file_names, self.mount_node_id)
        await self.graph.add_nodes(
            [LeafNodeCreate(
                entity_id=file_obj.id,
                name=file_obj.name,
                entity_type="data_source",
                parent_branch_nodes=[self.mount_node_id],
                x_position=400,
                y_position=400,
            ) for file_obj in file_objs]
        )
        await self.graph.create_edges(edges)
        return file_objs, file_paths

    async def describe_analysis(self, analysis_obj: Analysis, include_connections: bool = True) -> str:
        return await get_analysis_description(analysis_obj.id, self, include_connections=include_connections)
