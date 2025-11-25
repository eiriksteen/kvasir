from typing import Optional
from uuid import UUID

from kvasir_ontology.ontology import Ontology
from synesis_api.modules.data_sources.service import DataSources
from synesis_api.modules.analysis.service import Analyses
from synesis_api.modules.data_objects.service import Datasets
from synesis_api.modules.pipeline.service import Pipelines
from synesis_api.modules.model.service import Models
from synesis_api.modules.entity_graph.service import EntityGraphs
from synesis_api.modules.visualization.service import Visualizations
from synesis_api.modules.codebase.service import Codebase


def create_ontology_for_user(
    user_id: UUID,
    mount_group_id: UUID,
    bearer_token: Optional[str] = None
) -> Ontology:

    data_source_service = DataSources(user_id, bearer_token=bearer_token)
    analysis_service = Analyses(user_id)
    dataset_service = Datasets(user_id, bearer_token=bearer_token)
    pipeline_service = Pipelines(user_id)
    model_service = Models(user_id)
    graph_service = EntityGraphs(user_id)
    visualization_service = Visualizations(user_id)
    code_service = Codebase(user_id, mount_group_id)

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
