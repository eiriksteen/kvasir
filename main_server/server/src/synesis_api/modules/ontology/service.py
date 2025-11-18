from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends

from synesis_api.auth.service import get_current_user
from synesis_api.auth.schema import User
from kvasir_ontology.ontology import Ontology
from kvasir_ontology.entities.data_source.interface import DataSourceInterface
from kvasir_ontology.entities.analysis.interface import AnalysisInterface
from kvasir_ontology.entities.dataset.interface import DatasetInterface
from kvasir_ontology.entities.pipeline.interface import PipelineInterface
from kvasir_ontology.entities.model.interface import ModelInterface
from kvasir_ontology.visualization.interface import VisualizationInterface
from kvasir_ontology.graph.interface import GraphInterface
from kvasir_ontology.code.interface import CodeInterface
from kvasir_ontology.code.data_model import CodebaseFile, CodebasePath

from synesis_api.modules.data_sources.service import DataSources
from synesis_api.modules.analysis.service import Analyses
from synesis_api.modules.data_objects.service import Datasets
from synesis_api.modules.pipeline.service import Pipelines
from synesis_api.modules.model.service import Models
from synesis_api.modules.entity_graph.service import EntityGraphs
from synesis_api.modules.visualization.service import VisualizationService


class CodeService(CodeInterface):

    def __init__(self, user_id: UUID, mount_group_id: UUID):
        super().__init__(user_id, mount_group_id)
        self.user_id = user_id
        self.mount_group_id = mount_group_id

    async def get_codebase_tree(self) -> CodebasePath:
        return CodebasePath(
            path="/",
            is_file=False,
            sub_paths=[]
        )

    async def get_codebase_file(self, file_path: str) -> CodebaseFile:
        raise FileNotFoundError(f"File not found: {file_path}")


def create_ontology_for_user(
    user_id: UUID,
    mount_group_id: UUID,
    bearer_token: Optional[str] = None
) -> Ontology:
    data_source_service: DataSourceInterface = DataSources(
        user_id, bearer_token=bearer_token)
    analysis_service: AnalysisInterface = Analyses(user_id)
    dataset_service: DatasetInterface = Datasets(
        user_id, bearer_token=bearer_token)
    pipeline_service: PipelineInterface = Pipelines(user_id)
    model_service: ModelInterface = Models(user_id)
    graph_service: GraphInterface = EntityGraphs(user_id)
    visualization_service: VisualizationInterface = VisualizationService(
        user_id)
    code_service: CodeInterface = CodeService(user_id, mount_group_id)

    return Ontology(
        user_id=user_id,
        mount_group_id=mount_group_id,
        data_source_interface=data_source_service,
        analysis_interface=analysis_service,
        dataset_interface=dataset_service,
        pipeline_interface=pipeline_service,
        model_interface=model_service,
        visualization_interface=visualization_service,
        graph_interface=graph_service,
        code_interface=code_service
    )
