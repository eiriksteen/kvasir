import uuid
import asyncio
from pathlib import Path
from typing import Optional, List
from pydantic_ai import RunContext, ModelRetry, FunctionToolset

from kvasir_research.utils.code_utils import remove_print_statements_from_code
from kvasir_research.agents.v1.analysis.deps import AnalysisDeps
from kvasir_research.agents.v1.chart.agent import ChartAgentV1, ChartDeps
from kvasir_research.agents.v1.base_agent import Context

from kvasir_ontology.entities.analysis.data_model import (
    SectionCreate, CodeCellCreate, MarkdownCellCreate, CodeOutputCreate, AnalysisCell, Analysis, Section)
from kvasir_ontology.visualization.data_model import ImageCreate, TableCreate, EchartCreate
from kvasir_research.secrets import SANDBOX_INTERNAL_SCRIPT_DIR


async def create_section(ctx: RunContext[AnalysisDeps], section_name: str, order: Optional[int] = None) -> str:
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Creating section: {section_name}", "tool_call")
    _validate_section_order(ctx, order)

    created_section = await ctx.deps.ontology.analyses.create_section(SectionCreate(
        name=section_name,
        analysis_id=ctx.deps.analysis.id,
        description=None,
        code_cells_create=[],
        markdown_cells_create=[],
        order=order
    ))

    _update_analysis_object_with_section(ctx.deps.analysis, created_section)
    await ctx.deps.ontology.analyses.write_to_analysis_stream(ctx.deps.run_id, created_section)
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Created section: {section_name}", "result")
    return await _describe_current_run(ctx)


async def delete_section(ctx: RunContext[AnalysisDeps], section_id: uuid.UUID) -> str:
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Deleting section {section_id}", "tool_call")

    _validate_section_exists(ctx, section_id)
    await ctx.deps.ontology.analyses.delete_sections([section_id])
    _delete_section_from_analysis_object(ctx.deps.analysis, section_id)
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Deleted section {section_id}", "result")
    return await _describe_current_run(ctx)


async def create_code_cell(
    ctx: RunContext[AnalysisDeps],
    code: str,
    section_id: uuid.UUID,
    order: Optional[int] = None,
    table_paths: Optional[List[str]] = None,
    plot_paths: Optional[List[str]] = None,
    charts_to_create_descriptions: Optional[List[str]] = None
) -> str:
    """Create a new code cell in the analysis notebook. If order is None, the cell will be added at the end of the section. If not it will be inserted at the given order."""
    _validate_paths((table_paths or []) + (plot_paths or []))
    _validate_section_exists(ctx, section_id)
    _validate_cell_order(ctx, section_id, order)

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Creating code cell in section {section_id} {code}", "tool_call")

    past_code = _extract_code_from_previous_cells(
        ctx.deps.analysis, remove_print_statements=True)
    full_code = f"{past_code}\n\n{code}"

    out, err = await ctx.deps.sandbox.run_python_code(
        full_code,
        truncate_output=True,
        timeout=ctx.deps.time_limit
    )

    if err:
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Error executing code cell: {err}", "error")
        raise ModelRetry(f"Error executing code cell: {err}")

    analysis_cell = await ctx.deps.ontology.analyses.create_code_cell(CodeCellCreate(
        section_id=section_id,
        code=code,
        order=order,
        output=CodeOutputCreate(
            output=out,
            images=[ImageCreate(image_path=plot_path)
                    for plot_path in (plot_paths or [])],
            tables=[TableCreate(table_path=table_path)
                    for table_path in (table_paths or [])]
        )
    ))

    _update_analysis_object_with_cell(ctx.deps.analysis, analysis_cell)

    if charts_to_create_descriptions:
        for chart_description in charts_to_create_descriptions:
            asyncio.create_task(_add_analysis_chart(
                ctx, analysis_cell.id, chart_description))

    await ctx.deps.ontology.analyses.write_to_analysis_stream(ctx.deps.run_id, analysis_cell)

    total_cells = sum(len(s.cells) for s in ctx.deps.analysis.sections)
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Created code cell (output: {len(out)} characters, total cells: {total_cells})", "result")
    return await _describe_current_run(ctx)


async def create_markdown_cell(
    ctx: RunContext[AnalysisDeps],
    content: str,
    section_id: uuid.UUID,
    order: Optional[int] = None
) -> str:
    """Create a new markdown cell in the analysis notebook. If order is None, the cell will be added at the end of the section. If not it will be inserted at the given order."""
    _validate_section_exists(ctx, section_id)
    _validate_cell_order(ctx, section_id, order)

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Creating markdown cell in section {section_id} {content}", "tool_call")

    analysis_cell = await ctx.deps.ontology.analyses.create_markdown_cell(MarkdownCellCreate(
        section_id=section_id,
        markdown=content,
        order=order
    ))

    _update_analysis_object_with_cell(ctx.deps.analysis, analysis_cell)

    await ctx.deps.ontology.analyses.write_to_analysis_stream(ctx.deps.run_id, analysis_cell)

    total_cells = sum(len(s.cells) for s in ctx.deps.analysis.sections)
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Created markdown cell (total cells: {total_cells})", "result")
    return await _describe_current_run(ctx)


async def delete_cell(ctx: RunContext[AnalysisDeps], cell_id: uuid.UUID) -> str:
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Deleting cell {cell_id}", "tool_call")

    cell_found = False
    deleted_order = None
    for section in ctx.deps.analysis.sections:
        for cell in section.cells:
            if cell.id == cell_id:
                deleted_order = cell.order
                section.cells.remove(cell)
                cell_found = True
                for remaining_cell in section.cells:
                    if remaining_cell.order > deleted_order:
                        remaining_cell.order -= 1
                break
        if cell_found:
            break

    if not cell_found:
        raise ModelRetry(
            f"Cell with ID '{cell_id}' does not exist in the analysis. Available cell IDs: {', '.join([str(cell.id) for section in ctx.deps.analysis.sections for cell in section.cells])}")

    await ctx.deps.ontology.analyses.delete_cells([cell_id])
    _delete_cell_from_analysis_object(ctx.deps.analysis, cell_id)
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Deleted cell {cell_id}", "result")
    return await _describe_current_run(ctx)


analysis_toolset = FunctionToolset(
    tools=[
        create_section,
        delete_section,
        create_code_cell,
        create_markdown_cell,
        delete_cell
    ],
    max_retries=3
)


###


def _extract_code_from_previous_cells(analysis: Analysis, remove_print_statements: bool = True) -> str:
    code_cells = [
        cell.type_fields.code for section in analysis.sections for cell in section.cells if cell.type == "code"
    ]
    code_combined = "\n\n".join(code_cells)
    if remove_print_statements:
        code_combined = remove_print_statements_from_code(code_combined)
    return code_combined


async def _add_analysis_chart(ctx: RunContext[AnalysisDeps], cell_id: uuid.UUID, chart_description: str) -> None:
    deps = ChartDeps(
        user_id=ctx.deps.user_id,
        project_id=ctx.deps.project_id,
        package_name=ctx.deps.package_name,
        sandbox_type=ctx.deps.sandbox_type,
        callbacks=ctx.deps.callbacks,
        bearer_token=ctx.deps.bearer_token,
        base_code=_extract_code_from_previous_cells(
            ctx.deps.analysis, remove_print_statements=True))

    chart_agent = ChartAgentV1(deps)
    chart_output = await chart_agent(chart_description, Context(analyses=[ctx.deps.analysis.id]))
    save_path = SANDBOX_INTERNAL_SCRIPT_DIR / f"{cell_id}_{uuid.uuid4()}.py"
    await ctx.deps.sandbox.write_file(str(save_path), chart_output.script_content)
    await ctx.deps.ontology.analyses.create_code_output_echart(cell_id, EchartCreate(chart_script_path=str(save_path)))


def _update_analysis_object_with_cell(analysis: Analysis, cell: AnalysisCell):
    # 1: order is at the end of section, in case simply append
    # 2: order is before end, in which case we need to shift all cells after
    section = next(
        (s for s in analysis.sections if s.id == cell.section_id), None)
    if section:
        cell_exists = any(c.id == cell.id for c in section.cells)
        if cell_exists:
            section.cells = [c if c.id !=
                             cell.id else cell for c in section.cells]
        elif cell.order == len(section.cells):
            section.cells.append(cell)
        else:
            for c in section.cells:
                if c.order >= cell.order:
                    c.order += 1
            section.cells.append(cell)

        section.cells.sort(key=lambda c: c.order)


def _delete_cell_from_analysis_object(analysis: Analysis, cell_id: uuid.UUID):
    # Need to shift all sections after, if any
    section = next((s for s in analysis.sections if any(
        c.id == cell_id for c in s.cells)), None)
    if section:
        cell = next((c for c in section.cells if c.id == cell_id), None)
        if cell:
            section.cells.remove(cell)
            for c in section.cells:
                if c.order > cell.order:
                    c.order -= 1
            section.cells.sort(key=lambda c: c.order)


def _update_analysis_object_with_section(analysis: Analysis, section: Section):
    # 1: order is at the end of analysis, in case simply append
    # 2: order is before end, in which case we need to shift all sections after
    section_exists = any(s.id == section.id for s in analysis.sections)
    if section_exists:
        analysis.sections = [s if s.id !=
                             section.id else section for s in analysis.sections]
    elif section.order == len(analysis.sections):
        analysis.sections.append(section)
    else:
        for s in analysis.sections:
            if s.order >= section.order:
                s.order += 1
        analysis.sections.append(section)

    analysis.sections.sort(key=lambda s: s.order)


def _delete_section_from_analysis_object(analysis: Analysis, section_id: uuid.UUID):
    # Need to shift all sections after, if any
    section = next((s for s in analysis.sections if s.id == section_id), None)
    if section:
        deleted_order = section.order
        analysis.sections.remove(section)
        for s in analysis.sections:
            if s.order > deleted_order:
                s.order -= 1
        analysis.sections.sort(key=lambda s: s.order)


async def _describe_current_run(ctx: RunContext[AnalysisDeps]) -> str:
    analysis_desc = await ctx.deps.ontology.describe_analysis(ctx.deps.analysis)
    full_desc = f"Current run ID: {ctx.deps.run_id}\n\nCurrent run name: {ctx.deps.run_name}\n\nCurrent analysis:\n\n{analysis_desc}"
    return full_desc


def _validate_paths(paths: List[str | Path]):
    for path in paths:
        path = Path(path)
        if path.name.startswith("%"):
            raise ModelRetry(f"Path {path} is not valid. It starts with %")
        elif not path.is_absolute():
            raise ModelRetry(f"Path {path} is not absolute")


def _validate_section_exists(ctx: RunContext[AnalysisDeps], section_id: uuid.UUID) -> None:
    for section in ctx.deps.analysis.sections:
        if section.id == section_id:
            return
    raise ModelRetry(f"Section {section_id} not found")


def _validate_section_order(ctx: RunContext[AnalysisDeps], order: Optional[int] = None) -> None:
    if not order:
        return
    # needs to be between 0 and the number of sections (inclusive, to allow appending at the end)
    if order < 0 or order > len(ctx.deps.analysis.sections):
        raise ModelRetry(
            f"Section order {order} is not valid. It must be between 0 and {len(ctx.deps.analysis.sections)}")
    for section in ctx.deps.analysis.sections:
        if section.order == order:
            raise ModelRetry(f"Section order {order} is already taken")


def _validate_cell_order(ctx: RunContext[AnalysisDeps], section_id: uuid.UUID, order: Optional[int] = None) -> None:
    # for the given section, needs to be between 0 and the number of cells (inclusive, to allow appending at the end)
    if not order:
        return
    section = next(s for s in ctx.deps.analysis.sections if s.id == section_id)
    if order < 0 or order > len(section.cells):
        raise ModelRetry(
            f"Cell order {order} is not valid. It must be between 0 and {len(section.cells)}")
    for cell in section.cells:
        if cell.order == order:
            raise ModelRetry(f"Cell order {order} is already taken")
