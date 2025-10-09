# Import client
from .client import ProjectClient, FileInput

# Import all functions from request modules
from .requests.auth import (
    post_login,
    post_refresh,
    post_register,
    get_current_user,
    get_jwks
)

from .requests.runs import (
    post_run,
    post_run_message,
    post_run_message_pydantic,
    patch_run_status,
    post_data_integration_run_input,
    post_data_integration_run_result,
    get_runs,
    get_run_messages,
    get_run_messages_pydantic
)

from .requests.pipeline import (
    get_user_pipelines,
    get_user_pipeline,
    post_pipeline,
)

from .requests.orchestrator import (
    post_conversation,
    get_messages,
    get_conversations,
    create_chat_message_pydantic_request,
    create_context_request
)

from .requests.node import (
    post_create_node,
    get_project_nodes,
    put_update_node,
    delete_node
)

from .requests.data_sources import (
    get_data_sources,
    get_data_sources_by_ids,
    post_file_data_source,
    post_data_source_analysis,
    post_data_source_details
)

from .requests.data_objects import (
    post_dataset,
    get_project_datasets,
    get_dataset,
    get_object_group,
    get_object_groups_in_dataset,
    get_datasets_by_ids,
    create_aggregation_object_request,
    update_aggregation_object_request,
    get_aggregation_object_by_analysis_result_id_request
)

from .requests.project import (
    post_create_project,
    get_project,
    put_update_project,
    post_add_entity,
    delete_remove_entity,
    delete_project,
    get_user_projects
)

from .requests.knowledge_bank import (
    post_search_functions,
    post_search_models,
    post_search_model_sources
)

from .requests.function import (
    post_function
)

from .requests.model import (
    post_model,
    post_model_entity,
    get_project_model_entities,
    get_model_entities_by_ids
)

from .requests.model_sources import (
    get_model_source,
    post_model_source
)

from .requests.analysis import (
    get_analysis_objects_by_project_request,
    get_analysis_object_request,
    create_section_request,
    update_section_request,
    delete_section_request,
    add_analysis_result_to_section_request,
    get_data_for_analysis_result_request,
    move_element_request,
    update_analysis_result_request,
    delete_analysis_result_request,
    create_analysis_result_request,
    create_analysis_run_request,
    get_analysis_result_by_id_request,
    get_analysis_results_by_ids_request
)

from .requests.plots import (
    create_plot,
    update_plot,
    delete_plot,
    get_plot,
    get_plots_by_analysis_result
)

from .requests.tables import (
    create_table,
    get_tables_by_analysis_result_id,
    delete_table,
    update_table
)

# Export all functions and classes
__all__ = [
    # Client
    "ProjectClient",

    # Auth functions
    "post_login",
    "post_refresh",
    "post_register",
    "get_current_user",
    "get_jwks",

    # Runs functions
    "post_run",
    "post_run_message",
    "post_run_message_pydantic",
    "patch_run_status",
    "post_data_integration_run_input",
    "post_data_integration_run_result",
    "get_runs",
    "get_run_messages",
    "get_run_messages_pydantic",

    # Pipeline functions
    "get_user_pipelines",
    "get_user_pipeline",
    "post_pipeline",
    "post_function",
    "post_model",
    "post_model_entity",

    # Function functions
    "post_function",

    # Model functions
    "post_model",
    "post_model_entity",
    "get_project_model_entities",
    "get_model_entities_by_ids",

    # Orchestrator functions
    "post_conversation",
    "get_messages",
    "get_conversations",
    "create_chat_message_pydantic_request",
    "create_context_request",

    # Node functions
    "post_create_node",
    "get_project_nodes",
    "put_update_node",
    "delete_node",

    # Data sources functions
    "get_data_sources",
    "get_data_sources_by_ids",
    "post_file_data_source",
    "post_data_source_analysis",
    "post_data_source_details",

    # Data objects functions
    "post_dataset",
    "get_project_datasets",
    "get_dataset",
    "get_object_group",
    "get_object_groups_in_dataset",
    "get_time_series_data",
    "create_aggregation_object_request",
    "update_aggregation_object_request",
    "get_aggregation_object_by_analysis_result_id_request",

    # Project functions
    "post_create_project",
    "get_project",
    "put_update_project",
    "post_add_entity",
    "delete_remove_entity",
    "delete_project",
    "get_user_projects",

    # Knowledge bank functions
    "post_search_functions",

    # Analysis functions
    "get_analysis_objects_by_project_request",
    "get_analysis_object_request",
    "create_section_request",
    "update_section_request",
    "delete_section_request",
    "add_analysis_result_to_section_request",
    "get_data_for_analysis_result_request",
    "move_element_request",
    "update_analysis_result_request",
    "delete_analysis_result_request",
    "create_analysis_result_request",
    "create_analysis_run_request",
    "get_analysis_result_by_id_request",
    "get_analysis_results_by_ids_request"

    # Plots functions
    "create_plot",
    "update_plot",
    "delete_plot",
    "get_plot",
    "get_plots_by_analysis_result_id"

    # Tables functions
    "create_table",
    "get_tables_by_analysis_result_id",
    "delete_table",
    "update_table"
]
