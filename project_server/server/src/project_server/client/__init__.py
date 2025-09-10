# Import client
from .client import ProjectClient

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
    post_function
)

from .requests.orchestrator import (
    post_conversation,
    get_messages,
    get_conversations
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
    get_datasets,
    get_dataset,
    get_object_group,
    get_object_groups_in_dataset
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
    post_search_functions
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

    # Orchestrator functions
    "post_conversation",
    "get_messages",
    "get_conversations",

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
    "get_datasets",
    "get_dataset",
    "get_object_group",
    "get_object_groups_in_dataset",
    "get_time_series_data",

    # Project functions
    "post_create_project",
    "get_project",
    "put_update_project",
    "post_add_entity",
    "delete_remove_entity",
    "delete_project",
    "get_user_projects",

    # Knowledge bank functions
    "post_search_functions"
]
