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
    get_runs,
    get_run_messages,
    get_run_messages_pydantic
)

from .requests.pipeline import (
    get_user_pipelines,
    get_user_pipeline,
    post_pipeline,
    post_pipeline_output_model_entity,
    post_pipeline_output_dataset,
    post_pipeline_run_object,
    patch_pipeline_run_status,
    post_pipeline_implementation
)

from .requests.orchestrator import (
    post_conversation,
    get_messages,
    get_conversations,
    create_chat_message_pydantic_request,
    create_context_request,
    submit_swe_result_approval_request
)


from .requests.data_sources import (
    get_data_sources,
    get_data_sources_by_ids,
    post_file_data_source,
    post_data_source_analysis,
    post_data_source_details,
    get_data_source
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
    get_aggregation_object_by_analysis_result_id_request,
)

from .requests.project import (
    post_create_project,
    get_project,
    put_update_project,
    post_add_entity,
    delete_entity,
    delete_project,
    get_user_projects,
)

from .requests.knowledge_bank import (
    post_search_functions,
    post_search_models,
)

from .requests.function import (
    post_function,
    post_update_function,
    get_functions,
)

from .requests.model import (
    post_model,
    post_model_entity,
    post_model_entity_implementation,
    get_project_model_entities,
    get_model_entities_by_ids,
    patch_model_entity_config,
    post_update_model
)

from .requests.analysis import (
    get_analysis_objects_by_project_request,
    get_analysis_object_request,
    create_section_request,
    update_section_request,
    delete_section_request,
    add_analysis_result_to_section_request,
    move_element_request,
    update_analysis_result_request,
    delete_analysis_result_request,
    create_analysis_result_request,
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
    "post_pipeline_implementation",
    "post_pipeline_output_model_entity",
    "post_pipeline_output_dataset",
    "patch_pipeline_run_status",
    "post_function",
    "post_model",
    "post_model_entity",
    "post_pipeline_run_object",

    # Function functions
    "post_function",
    "post_update_function",
    "get_functions",
    # Model functions
    "post_model",
    "post_model_entity",
    "get_project_model_entities",
    "get_model_entities_by_ids",
    "patch_model_entity_config",
    "post_update_model",
    "get_model_source",
    "post_model_source",
    "get_model_sources",
    # Orchestrator functions
    "post_conversation",
    "get_messages",
    "get_conversations",
    "create_chat_message_pydantic_request",
    "create_context_request",

    # Data sources functions
    "get_data_sources",
    "get_data_sources_by_ids",
    "post_file_data_source",
    "post_data_source_analysis",
    "post_data_source_details",
    "get_data_sources_descriptions",
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
    "get_datasets_descriptions_request",
    # Project functions
    "post_create_project",
    "get_project",
    "put_update_project",
    "post_add_entity",
    "delete_entity",
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
