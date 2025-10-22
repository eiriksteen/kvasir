from typing import List

from synesis_schemas.main_server import DataSource, Dataset, ModelEntity


def get_object_group_imports() -> str:
    """
    Get the import statements for object group definitions.
    """
    return "from project_server.entity_manager import LocalDatasetManager"


def get_object_group_definitions(datasets: List[Dataset], bearer_token: str, num_tab_indents: int = 0) -> str:
    """
    Get the object group definitions for the datasets.
    bearer_token should be a variable name (e.g., 'bearer_token') that will be used as a reference in the generated code.
    """
    indent = "    " * num_tab_indents
    manager_definition = f"{indent}dataset_manager = LocalDatasetManager(bearer_token={bearer_token})\n"

    object_group_definitions = []
    for dataset in datasets:
        for object_group in dataset.object_groups:
            object_group_definitions.append(
                f"{indent}{dataset.name}_{object_group.name} = await dataset_manager.get_object_group_data_by_name(dataset_id='{dataset.id}', group_name='{object_group.name}')")

    return manager_definition + "\n".join(object_group_definitions)


def get_data_source_imports() -> str:
    """
    Get the import statements for data source definitions.
    """
    return "from project_server.entity_manager import DataSourceManager"


def get_data_source_definitions(data_sources: List[DataSource], bearer_token: str, num_tab_indents: int = 0) -> str:
    """
    Get the data source definitions for the data sources.
    bearer_token should be a variable name (e.g., 'bearer_token') that will be used as a reference in the generated code.
    """
    indent = "    " * num_tab_indents
    manager_definition = f"{indent}data_source_manager = DataSourceManager(bearer_token={bearer_token})\n"

    data_source_definitions = []
    for data_source in data_sources:
        data_source_definitions.append(
            f"{indent}{data_source.name} = await data_source_manager.get_data_source(data_source_id='{data_source.id}')")

    return manager_definition + "\n".join(data_source_definitions)


def get_model_entity_imports(model_entities: List[ModelEntity]) -> str:
    """
    Get the import statements for model entity definitions.
    """
    import_definitions = []
    for model_entity in model_entities:
        import_definitions.append(
            f"from {model_entity.implementation.model_implementation.implementation_script.module_path} import ModelConfig as ModelConfig{model_entity.implementation.model_implementation.python_class_name}")
    return "\n".join(import_definitions)


def get_model_entity_definitions(model_entities: List[ModelEntity], num_tab_indents: int = 0) -> str:
    """
    Get the model entity object definitions.
    """
    indent = "    " * num_tab_indents
    model_entity_definitions = []
    for model_entity in model_entities:
        model_entity_definitions.append(
            f"{indent}{model_entity.name} = {model_entity.implementation.model_implementation.python_class_name}(config=ModelConfig{model_entity.implementation.model_implementation.python_class_name}(**{model_entity.implementation.config}))")
    return "\n".join(model_entity_definitions)
