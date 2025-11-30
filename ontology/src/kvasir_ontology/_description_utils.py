from ast import Pass
import json
from typing import List, TYPE_CHECKING
from uuid import UUID


if TYPE_CHECKING:
    from kvasir_ontology.ontology import Ontology
    from kvasir_ontology.graph.data_model import CHILD_TYPE_LITERAL


def _is_simple_value(value) -> bool:
    value_str = str(value)
    return "\n" not in value_str and len(value_str) < 200


def _format_simple_field(name: str, value, indent: str = "") -> str:
    value_str = str(value).replace("'", "&apos;")
    return f"{indent}<{name}='{value_str}' />"


def _format_complex_field(name: str, value, indent: str = "", content_indent: str = "") -> List[str]:
    result = [f'{indent}<{name}>']
    value_str = str(value)
    for line in value_str.strip().split("\n"):
        result.append(f"{content_indent}{line}")
    result.append(f'{indent}</{name}>')
    return result


async def _get_connections_description(
    entity_id: UUID,
    ontology: "Ontology"
) -> List[str]:
    result = []

    leaf_node = await ontology.graph.get_leaf_node_by_entity_id(entity_id)

    num_inputs = sum([
        len(leaf_node.from_entities.data_sources),
        len(leaf_node.from_entities.datasets),
        len(leaf_node.from_entities.pipelines),
        len(leaf_node.from_entities.models_instantiated),
        len(leaf_node.from_entities.analyses),
    ])

    result.append("")
    result.append(
        f'  <inputs num_inputs="{num_inputs}">')

    for data_source_id in leaf_node.from_entities.data_sources:
        entity_desc = await get_data_source_description(
            data_source_id, ontology, include_connections=False)
        result.append("    <input>")
        for line in entity_desc.split("\n"):
            result.append(f"      {line}")
        result.append("    </input>")
    for dataset_id in leaf_node.from_entities.datasets:
        entity_desc = await get_dataset_description(
            dataset_id, ontology, include_connections=False)
        result.append("    <input>")
        for line in entity_desc.split("\n"):
            result.append(f"      {line}")
        result.append("    </input>")
    for pipeline_id in leaf_node.from_entities.pipelines:
        entity_desc = await get_pipeline_description(
            pipeline_id, ontology, include_connections=False, include_runs=False)
        result.append("    <input>")
        for line in entity_desc.split("\n"):
            result.append(f"      {line}")
        result.append("    </input>")
    for model_instantiated_id in leaf_node.from_entities.models_instantiated:
        entity_desc = await get_model_entity_description(
            model_instantiated_id, ontology, include_connections=False)
        result.append("    <input>")
        for line in entity_desc.split("\n"):
            result.append(f"      {line}")
        result.append("    </input>")
    for analysis_id in leaf_node.from_entities.analyses:
        entity_desc = await get_analysis_description(
            analysis_id, ontology, include_connections=False)
        result.append("    <input>")
        for line in entity_desc.split("\n"):
            result.append(f"      {line}")
        result.append("    </input>")

    result.append("  </inputs>")

    if leaf_node.entity_type == "pipeline":
        num_outputs = len(leaf_node.runs)
        result.append("")
        result.append(
            f'  <outputs num_outputs="{num_outputs}">')
        for run in leaf_node.runs:
            entity_desc = await get_pipeline_run_description(
                run.id, ontology, include_connections=False)
            result.append("    <output>")
            for line in entity_desc.split("\n"):
                result.append(f"      {line}")
            result.append("    </output>")
        result.append("  </outputs>")
    else:
        num_outputs = sum([
            len(leaf_node.to_entities.data_sources),
            len(leaf_node.to_entities.datasets),
            len(leaf_node.to_entities.pipelines),
            len(leaf_node.to_entities.models_instantiated),
            len(leaf_node.to_entities.analyses),
        ])

        result.append("")
        result.append(
            f'  <outputs num_outputs="{num_outputs}">')

        if leaf_node.to_entities:
            for data_source_id in leaf_node.to_entities.data_sources:
                entity_desc = await get_data_source_description(
                    data_source_id, ontology, include_connections=False)
                result.append("    <output>")
                for line in entity_desc.split("\n"):
                    result.append(f"      {line}")
                result.append("    </output>")
            for dataset_id in leaf_node.to_entities.datasets:
                entity_desc = await get_dataset_description(
                    dataset_id, ontology, include_connections=False)
                result.append("    <output>")
                for line in entity_desc.split("\n"):
                    result.append(f"      {line}")
                result.append("    </output>")
            for pipeline_id in leaf_node.to_entities.pipelines:
                entity_desc = await get_pipeline_description(
                    pipeline_id, ontology, include_connections=False, include_runs=False)
                result.append("    <output>")
                for line in entity_desc.split("\n"):
                    result.append(f"      {line}")
                result.append("    </output>")
            for model_instantiated_id in leaf_node.to_entities.models_instantiated:
                entity_desc = await get_model_entity_description(
                    model_instantiated_id, ontology, include_connections=False)
                result.append("    <output>")
                for line in entity_desc.split("\n"):
                    result.append(f"      {line}")
                result.append("    </output>")
            result.append("  </outputs>")

    return result


async def get_entity_description(entity_id: UUID, ontology: "Ontology", include_connections: bool = True) -> str:
    entity_graph = await ontology.get_entity_graph()

    def _get_entity_type(entity_id: UUID) -> CHILD_TYPE_LITERAL:
        for entity in entity_graph.data_sources:
            if entity.id == entity_id:
                return "data_source"
        for entity in entity_graph.datasets:
            if entity.id == entity_id:
                return "dataset"
        for entity in entity_graph.analyses:
            if entity.id == entity_id:
                return "analysis"
    pass


async def get_data_source_description(entity_id: UUID, ontology: "Ontology", include_connections: bool = True) -> str:
    data_sources = await ontology.data_sources.get_data_sources([entity_id])
    if not data_sources:
        raise ValueError(f"Data source with ID {entity_id} not found")
    data_source = data_sources[0]

    result = [f'<data_source id="{data_source.id}" name="{data_source.name}">']

    if data_source.description:
        result.append("")
        result.append("  <description>")
        for line in data_source.description.strip().split("\n"):
            result.append(f"    {line}")
        result.append("  </description>")

    if data_source.type_fields:
        result.append("")
        result.append("  <type_fields>")
        type_fields = data_source.type_fields
        if hasattr(type_fields, 'file_name'):
            result.append(_format_simple_field(
                'file_name', type_fields.file_name, "    "))
        if hasattr(type_fields, 'file_path'):
            result.append(_format_simple_field(
                'file_path', type_fields.file_path, "    "))
        if hasattr(type_fields, 'file_type'):
            result.append(_format_simple_field(
                'file_type', type_fields.file_type, "    "))
        if hasattr(type_fields, 'file_size_bytes'):
            result.append(_format_simple_field('file_size_bytes',
                          type_fields.file_size_bytes, "    "))
        result.append("  </type_fields>")

    if data_source.additional_variables:
        result.append("")
        result.append("  <additional_variables>")
        for key, value in data_source.additional_variables.items():
            if _is_simple_value(value):
                result.append(_format_simple_field(key, value, "    "))
            else:
                result.extend(_format_complex_field(
                    key, value, "    ", "      "))
        result.append("  </additional_variables>")

    if include_connections:
        connections = await _get_connections_description(entity_id, ontology)
        result.extend(connections)

    result.append("")
    result.append("</data_source>")

    return "\n".join(result)


async def get_dataset_description(entity_id: UUID, ontology: "Ontology", include_connections: bool = True) -> str:
    datasets = await ontology.datasets.get_datasets([entity_id])
    if not datasets:
        raise ValueError(f"Dataset with ID {entity_id} not found")
    dataset = datasets[0]

    result = [f'<dataset id="{dataset.id}" name="{dataset.name}">']

    if dataset.description:
        result.append("")
        result.append("  <description>")
        for line in dataset.description.strip().split("\n"):
            result.append(f"    {line}")
        result.append("  </description>")

    if dataset.additional_variables:
        result.append("")
        result.append("  <additional_variables>")
        for key, value in dataset.additional_variables.items():
            if _is_simple_value(value):
                result.append(_format_simple_field(key, value, "    "))
            else:
                result.extend(_format_complex_field(
                    key, value, "    ", "      "))
        result.append("  </additional_variables>")

    if dataset.object_groups:
        result.append("")
        result.append("  <object_groups>")
        for object_group in dataset.object_groups:
            result.append("")
            result.append(
                f'    <object_group group_id="{object_group.id}" group_name="{object_group.name}">')

            if object_group.description:
                result.append("      <description>")
                for line in object_group.description.strip().split("\n"):
                    result.append(f"        {line}")
                result.append("      </description>")

            result.append(_format_simple_field(
                'modality', object_group.modality, "      "))

            if object_group.additional_variables:
                result.append("      <additional_variables>")
                for key, value in object_group.additional_variables.items():
                    if _is_simple_value(value):
                        result.append(_format_simple_field(
                            key, value, "        "))
                    else:
                        result.extend(_format_complex_field(
                            key, value, "        ", "          "))
                result.append("      </additional_variables>")

            if object_group.modality_fields:
                result.append("      <modality_fields>")
                modality_fields = object_group.modality_fields

                if object_group.modality == "time_series":
                    if hasattr(modality_fields, 'total_timestamps'):
                        result.append(_format_simple_field(
                            'total_timestamps', modality_fields.total_timestamps, "        "))
                    if hasattr(modality_fields, 'number_of_series'):
                        result.append(_format_simple_field(
                            'number_of_series', modality_fields.number_of_series, "        "))
                    if hasattr(modality_fields, 'earliest_timestamp'):
                        result.append(_format_simple_field(
                            'earliest_timestamp', modality_fields.earliest_timestamp, "        "))
                    if hasattr(modality_fields, 'latest_timestamp'):
                        result.append(_format_simple_field(
                            'latest_timestamp', modality_fields.latest_timestamp, "        "))
                    if hasattr(modality_fields, 'sampling_frequency') and modality_fields.sampling_frequency:
                        result.append(_format_simple_field(
                            'sampling_frequency', modality_fields.sampling_frequency, "        "))
                    if hasattr(modality_fields, 'timezone') and modality_fields.timezone:
                        result.append(_format_simple_field(
                            'timezone', modality_fields.timezone, "        "))
                    if hasattr(modality_fields, 'features_schema') and modality_fields.features_schema:
                        schema_str = json.dumps(modality_fields.features_schema) if isinstance(
                            modality_fields.features_schema, dict) else str(modality_fields.features_schema)
                        if _is_simple_value(schema_str):
                            result.append(_format_simple_field(
                                'features_schema', schema_str, "        "))
                        else:
                            result.extend(_format_complex_field(
                                'features_schema', schema_str, "        ", "          "))

                elif object_group.modality == "tabular":
                    if hasattr(modality_fields, 'number_of_entities'):
                        result.append(_format_simple_field(
                            'number_of_entities', modality_fields.number_of_entities, "        "))
                    if hasattr(modality_fields, 'number_of_features'):
                        result.append(_format_simple_field(
                            'number_of_features', modality_fields.number_of_features, "        "))
                    if hasattr(modality_fields, 'features_schema'):
                        schema_str = json.dumps(modality_fields.features_schema) if isinstance(
                            modality_fields.features_schema, dict) else str(modality_fields.features_schema)
                        if _is_simple_value(schema_str):
                            result.append(_format_simple_field(
                                'features_schema', schema_str, "        "))
                        else:
                            result.extend(_format_complex_field(
                                'features_schema', schema_str, "        ", "          "))

                result.append("      </modality_fields>")

            result.append("    </object_group>")

        result.append("  </object_groups>")

    if include_connections:
        connections = await _get_connections_description(entity_id, ontology)
        result.extend(connections)

    result.append("")
    result.append("</dataset>")

    return "\n".join(result)


async def get_pipeline_description(entity_id: UUID, ontology: "Ontology", include_connections: bool = True, include_runs: bool = True) -> str:
    pipelines = await ontology.pipelines.get_pipelines([entity_id])
    if not pipelines:
        raise ValueError(f"Pipeline with ID {entity_id} not found")
    pipeline = pipelines[0]

    result = [f'<pipeline id="{pipeline.id}" name="{pipeline.name}">']

    if pipeline.description:
        result.append("")
        result.append("  <description>")
        for line in pipeline.description.strip().split("\n"):
            result.append(f"    {line}")
        result.append("  </description>")

    if pipeline.implementation:
        impl = pipeline.implementation
        result.append("")
        result.append("  <implementation>")

        if impl.python_function_name:
            result.append(_format_simple_field(
                'python_function_name', impl.python_function_name, "    "))
        if impl.docstring:
            result.extend(_format_complex_field(
                'docstring', impl.docstring, "    ", "      "))
        if impl.description:
            result.extend(_format_complex_field(
                'description', impl.description, "    ", "      "))
        if impl.args_schema:
            schema_str = json.dumps(impl.args_schema) if isinstance(
                impl.args_schema, dict) else str(impl.args_schema)
            if _is_simple_value(schema_str):
                result.append(_format_simple_field(
                    'args_schema', schema_str, "    "))
            else:
                result.extend(_format_complex_field(
                    'args_schema', schema_str, "    ", "      "))
        if impl.default_args:
            args_str = json.dumps(impl.default_args) if isinstance(
                impl.default_args, dict) else str(impl.default_args)
            if _is_simple_value(args_str):
                result.append(_format_simple_field(
                    'default_args', args_str, "    "))
            else:
                result.extend(_format_complex_field(
                    'default_args', args_str, "    ", "      "))
        if impl.output_variables_schema:
            schema_str = json.dumps(impl.output_variables_schema) if isinstance(
                impl.output_variables_schema, dict) else str(impl.output_variables_schema)
            if _is_simple_value(schema_str):
                result.append(_format_simple_field(
                    'output_variables_schema', schema_str, "    "))
            else:
                result.extend(_format_complex_field(
                    'output_variables_schema', schema_str, "    ", "      "))

        if impl.implementation_script_path:
            result.append(_format_simple_field(
                'implementation_script_path', impl.implementation_script_path, "    "))
            code_file = await ontology.code.get_codebase_file(impl.implementation_script_path)
            result.append("    <code>")
            for line in code_file.content.split("\n"):
                result.append(f"      {line}")
            result.append("    </code>")

        result.append("  </implementation>")

    if include_connections:
        connections = await _get_connections_description(entity_id, ontology)
        result.extend(connections)

    if include_runs and pipeline.runs:
        result.append("")
        result.append("  <pipeline_runs>")
        for run in pipeline.runs:
            run_desc = await get_pipeline_run_description(
                run.id, ontology,
                show_pipeline_description=False,
                include_connections=False
            )
            result.append("")
            result.append("    <pipeline_run>")
            for line in run_desc.split("\n"):
                result.append(f"      {line}")
            result.append("    </pipeline_run>")
        result.append("  </pipeline_runs>")

    result.append("")
    result.append("</pipeline>")

    return "\n".join(result)


async def get_pipeline_run_description(
    run_id: UUID,
    ontology: "Ontology",
    show_pipeline_description: bool = True,
    include_connections: bool = True
) -> str:
    pipeline_run = await ontology.pipelines.get_pipeline_run(run_id)
    if not pipeline_run:
        raise ValueError(f"Pipeline run with ID {run_id} not found")

    run_name = pipeline_run.name or f"Run {pipeline_run.id}"
    result = [f'<pipeline_run id="{pipeline_run.id}" name="{run_name}">']

    if pipeline_run.description:
        result.append("")
        result.append("  <description>")
        for line in pipeline_run.description.strip().split("\n"):
            result.append(f"    {line}")
        result.append("  </description>")

    result.append("")
    result.append(_format_simple_field('status', pipeline_run.status, "  "))
    result.append("")
    result.append(_format_simple_field(
        'start_time', pipeline_run.start_time.isoformat(), "  "))
    if pipeline_run.end_time:
        result.append("")
        result.append(_format_simple_field(
            'end_time', pipeline_run.end_time.isoformat(), "  "))

    if pipeline_run.args:
        args_str = json.dumps(pipeline_run.args) if isinstance(
            pipeline_run.args, dict) else str(pipeline_run.args)
        result.append("")
        if _is_simple_value(args_str):
            result.append(_format_simple_field('args', args_str, "  "))
        else:
            result.extend(_format_complex_field(
                'args', args_str, "  ", "    "))

    if pipeline_run.output_variables:
        output_str = json.dumps(pipeline_run.output_variables) if isinstance(
            pipeline_run.output_variables, dict) else str(pipeline_run.output_variables)
        result.append("")
        if _is_simple_value(output_str):
            result.append(_format_simple_field(
                'output_variables', output_str, "  "))
        else:
            result.extend(_format_complex_field(
                'output_variables', output_str, "  ", "    "))

    if pipeline_run.execution_command:
        result.append("")
        if _is_simple_value(pipeline_run.execution_command):
            result.append(_format_simple_field(
                'execution_command', pipeline_run.execution_command, "  "))
        else:
            result.extend(_format_complex_field(
                'execution_command', pipeline_run.execution_command, "  ", "    "))

    if pipeline_run.terminal_output:
        result.append("")
        if _is_simple_value(pipeline_run.terminal_output):
            result.append(_format_simple_field(
                'terminal_output', pipeline_run.terminal_output, "  "))
        else:
            result.extend(_format_complex_field(
                'terminal_output', pipeline_run.terminal_output, "  ", "    "))

    if show_pipeline_description:
        result.append("")
        result.append("  <pipeline>")
        pipeline_desc = await get_pipeline_description(
            pipeline_run.pipeline_id, ontology,
            include_connections=False,
            include_runs=False
        )
        for line in pipeline_desc.split("\n"):
            result.append(f"    {line}")
        result.append("  </pipeline>")

    if include_connections:
        connections = await _get_connections_description(run_id, ontology)
        result.extend(connections)

    result.append("")
    result.append("</pipeline_run>")

    return "\n".join(result)


async def get_model_entity_description(entity_id: UUID, ontology: "Ontology", include_connections: bool = True) -> str:
    models = await ontology.models.get_models_instantiated([entity_id])
    if not models:
        raise ValueError(f"Model instantiated with ID {entity_id} not found")
    model_entity = models[0]

    result = [
        f'<model_instantiated id="{model_entity.id}" name="{model_entity.name}">']

    if model_entity.description:
        result.append("")
        result.append("  <description>")
        for line in model_entity.description.strip().split("\n"):
            result.append(f"    {line}")
        result.append("  </description>")

    if model_entity.config:
        config_str = json.dumps(model_entity.config) if isinstance(
            model_entity.config, dict) else str(model_entity.config)
        result.append("")
        if _is_simple_value(config_str):
            result.append(_format_simple_field('config', config_str, "  "))
        else:
            result.extend(_format_complex_field(
                'config', config_str, "  ", "    "))
    if model_entity.weights_save_dir:
        result.append("")
        result.append(_format_simple_field('weights_save_dir',
                      model_entity.weights_save_dir, "  "))

    if model_entity.model and model_entity.model.implementation:
        model_impl = model_entity.model.implementation
        result.append("")
        result.append("  <model_implementation>")

        if model_impl.id:
            result.append(_format_simple_field('id', model_impl.id, "    "))
        if model_impl.python_class_name:
            result.append(_format_simple_field(
                'python_class_name', model_impl.python_class_name, "    "))
        if model_impl.modality:
            result.append(_format_simple_field(
                'modality', model_impl.modality, "    "))
        if model_impl.task:
            result.append(_format_simple_field(
                'task', model_impl.task, "    "))
        if model_impl.model_class_docstring:
            result.extend(_format_complex_field(
                'model_class_docstring', model_impl.model_class_docstring, "    ", "      "))

        if model_impl.implementation_script_path:
            result.append(_format_simple_field(
                'implementation_script_path', model_impl.implementation_script_path, "    "))
            code_file = await ontology.code.get_codebase_file(model_impl.implementation_script_path)
            result.append("    <code>")
            for line in code_file.content.split("\n"):
                result.append(f"      {line}")
            result.append("    </code>")

        training_function = model_impl.training_function
        result.append("")
        result.append("    <training_function>")
        if training_function.docstring:
            result.extend(_format_complex_field(
                'docstring', training_function.docstring, "      ", "        "))
        if training_function.args_schema:
            schema_str = json.dumps(training_function.args_schema) if isinstance(
                training_function.args_schema, dict) else str(training_function.args_schema)
            if _is_simple_value(schema_str):
                result.append(_format_simple_field(
                    'args_schema', schema_str, "      "))
            else:
                result.extend(_format_complex_field(
                    'args_schema', schema_str, "      ", "        "))
        if training_function.default_args:
            args_str = json.dumps(training_function.default_args) if isinstance(
                training_function.default_args, dict) else str(training_function.default_args)
            if _is_simple_value(args_str):
                result.append(_format_simple_field(
                    'default_args', args_str, "      "))
            else:
                result.extend(_format_complex_field(
                    'default_args', args_str, "      ", "        "))
        if training_function.output_variables_schema:
            schema_str = json.dumps(training_function.output_variables_schema) if isinstance(
                training_function.output_variables_schema, dict) else str(training_function.output_variables_schema)
            if _is_simple_value(schema_str):
                result.append(_format_simple_field(
                    'output_variables_schema', schema_str, "      "))
            else:
                result.extend(_format_complex_field(
                    'output_variables_schema', schema_str, "      ", "        "))
        result.append("    </training_function>")

        inference_function = model_impl.inference_function
        result.append("")
        result.append("    <inference_function>")
        if inference_function.docstring:
            result.extend(_format_complex_field(
                'docstring', inference_function.docstring, "      ", "        "))
        if inference_function.args_schema:
            schema_str = json.dumps(inference_function.args_schema) if isinstance(
                inference_function.args_schema, dict) else str(inference_function.args_schema)
            if _is_simple_value(schema_str):
                result.append(_format_simple_field(
                    'args_schema', schema_str, "      "))
            else:
                result.extend(_format_complex_field(
                    'args_schema', schema_str, "      ", "        "))
        if inference_function.default_args:
            args_str = json.dumps(inference_function.default_args) if isinstance(
                inference_function.default_args, dict) else str(inference_function.default_args)
            if _is_simple_value(args_str):
                result.append(_format_simple_field(
                    'default_args', args_str, "      "))
            else:
                result.extend(_format_complex_field(
                    'default_args', args_str, "      ", "        "))
        if inference_function.output_variables_schema:
            schema_str = json.dumps(inference_function.output_variables_schema) if isinstance(
                inference_function.output_variables_schema, dict) else str(inference_function.output_variables_schema)
            if _is_simple_value(schema_str):
                result.append(_format_simple_field(
                    'output_variables_schema', schema_str, "      "))
            else:
                result.extend(_format_complex_field(
                    'output_variables_schema', schema_str, "      ", "        "))
        result.append("    </inference_function>")

        result.append("  </model_implementation>")

    if include_connections:
        connections = await _get_connections_description(entity_id, ontology)
        result.extend(connections)

    result.append("")
    result.append("</model_instantiated>")

    return "\n".join(result)


async def get_analysis_description(entity_id: UUID, ontology: "Ontology", include_connections: bool = True) -> str:
    analyses = await ontology.analyses.get_analyses([entity_id])
    if not analyses:
        raise ValueError(f"Analysis with ID {entity_id} not found")
    analysis = analyses[0]

    result = [f'<analysis id="{analysis.id}" name="{analysis.name}">']

    if analysis.description:
        result.append("")
        result.append("  <description>")
        for line in analysis.description.strip().split("\n"):
            result.append(f"    {line}")
        result.append("  </description>")

    if analysis.sections:
        for section in analysis.sections:
            result.append("")
            result.append(
                f'  <section name="{section.name}" section_id="{section.id}" order="{section.order}">')

            if section.description:
                result.append("    <section_description>")
                for line in section.description.strip().split("\n"):
                    result.append(f"      {line}")
                result.append("    </section_description>")

            for cell in sorted(section.cells, key=lambda c: c.order):
                if cell.type == "markdown":
                    result.append("")
                    result.append(
                        f'    <markdown id="{cell.id} order="{cell.order}">')
                    markdown_content = cell.type_fields.markdown
                    for line in markdown_content.strip().split("\n"):
                        result.append(f"      {line}")
                    result.append("    </markdown>")

                elif cell.type == "code":
                    result.append("")
                    result.append(
                        f'    <code id="{cell.id}" order="{cell.order}">')
                    code_content = cell.type_fields.code
                    for line in code_content.strip().split("\n"):
                        result.append(f"      {line}")
                    result.append("    </code>")

                    if cell.type_fields.output and cell.type_fields.output.output:
                        result.append("")
                        result.append("    <output>")
                        output_content = cell.type_fields.output.output
                        for line in output_content.strip().split("\n"):
                            result.append(f"      {line}")
                        result.append("    </output>")

            result.append("  </section>")
    else:
        result.append("")
        result.append("  (empty notebook)")

    if include_connections:
        connections = await _get_connections_description(entity_id, ontology)
        result.extend(connections)

    result.append("")
    result.append("</analysis>")

    return "\n".join(result)
