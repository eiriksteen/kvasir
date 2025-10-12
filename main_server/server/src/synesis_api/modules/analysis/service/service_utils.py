import uuid
from datetime import datetime
from sqlalchemy import select, and_
from typing import List, Tuple, Literal, Any


from synesis_api.database.service import fetch_one
from synesis_api.modules.analysis.models import (
    analysis_result, 
    notebook_section,
)
from synesis_schemas.main_server import (
    AnalysisObjectInDB, 
    AnalysisResult,
    NotebookSection,
    Notebook,
    AnalysisObject
)

async def get_prev_element(this_id: uuid.UUID, this_type: Literal['analysis_result', 'notebook_section'], section_id: uuid.UUID) -> Tuple[Literal['analysis_result', 'notebook_section'], uuid.UUID] | Tuple[None, None]:
    analysis_result_from_db = await fetch_one(select(analysis_result).where(and_(analysis_result.c.next_type == this_type, analysis_result.c.next_id == this_id, analysis_result.c.section_id == section_id)))
    if analysis_result_from_db:
        return "analysis_result", analysis_result_from_db["id"]
    notebook_section_from_db = await fetch_one(select(notebook_section).where(and_(notebook_section.c.next_type == this_type, notebook_section.c.next_id == this_id, notebook_section.c.parent_section_id == section_id)))
    if notebook_section_from_db:
        return "notebook_section", notebook_section_from_db["id"]
    return None, None


async def get_last_element_in_section(section_id: uuid.UUID, notebook_id: uuid.UUID | None = None) -> Tuple[Literal['analysis_result', 'notebook_section'], uuid.UUID] | Tuple[None, None]:
    """
    Gets all the analysis results and notebook sections in the given section and returns the type of the element and the 
    id of the element which does not have a next element.
    """
    result = await fetch_one(
        select(analysis_result).where(and_(analysis_result.c.section_id == section_id, analysis_result.c.next_id == None))
    )
    if result:
        return "analysis_result", result["id"]
    # Only need the notebook_id if we are getting the last element in a section that is a root section (no parent section) otherwise it may get a section from a different analysis object/notebook
    result = await fetch_one(
        select(notebook_section).where(and_(notebook_section.c.parent_section_id == section_id, notebook_section.c.next_id == None, notebook_section.c.notebook_id == notebook_id))
    )
    if result:
        return "notebook_section", result["id"]
    return None, None


def build_ordered_list(sections: List[NotebookSection], results: List[AnalysisResult], first_id: uuid.UUID | None, first_type: str | None) -> List[dict]:
    """
    Build ordered list from nextType/nextId chain, similar to the client-side utils.ts function.
    Returns a list of dictionaries with 'type' and 'data' keys.
    """
    ordered_list = []
    sections_map = {s.id: s for s in sections}
    results_map = {r.id: r for r in results}
    
    current_id = first_id
    current_type = first_type
    
    while current_id and current_type:
        if current_type == "notebook_section":
            section = sections_map.get(current_id)
            if section:
                ordered_list.append({"type": "section", "data": section})
                current_id = section.next_id
                current_type = section.next_type
            else:
                break
        elif current_type == "analysis_result":
            result = results_map.get(current_id)
            if result:
                ordered_list.append({"type": "analysis_result", "data": result})
                current_id = result.next_id
                current_type = result.next_type
            else:
                break
        else:
            break
    
    return ordered_list


def _get_dataset_ids_from_section(section: NotebookSection) -> List[uuid.UUID]:
    dataset_ids = []
    for section in section.notebook_sections:
        dataset_ids.extend(_get_dataset_ids_from_section(section))
    for result in section.analysis_results:
        dataset_ids.extend(result.dataset_ids)
    return dataset_ids

def get_dataset_ids_from_analysis_object(analysis_object: AnalysisObject) -> List[uuid.UUID]:
    dataset_ids = []
    for section in analysis_object.notebook.notebook_sections:
        dataset_ids.extend(_get_dataset_ids_from_section(section))
    return dataset_ids


def _get_data_source_ids_from_section(section: NotebookSection) -> List[uuid.UUID]:
    data_source_ids = []
    for section in section.notebook_sections:
        data_source_ids.extend(_get_data_source_ids_from_section(section))
    for result in section.analysis_results:
        data_source_ids.extend(result.data_source_ids)
    return data_source_ids

def get_data_source_ids_from_analysis_object(analysis_object: AnalysisObject) -> List[uuid.UUID]:
    data_source_ids = []
    for section in analysis_object.notebook.notebook_sections:
        data_source_ids.extend(_get_data_source_ids_from_section(section))
    return data_source_ids

async def generate_notebook_report(analysis_object: AnalysisObjectInDB, notebook: Notebook, include_code: bool, user_id: uuid.UUID) -> str:
    """
    Generate a markdown report from the analysis object's notebook.
    
    Args:
        analysis_object: The analysis object containing the notebook
        include_code: Whether to include Python code in the report
        
    Returns:
        A markdown string representing the complete analysis report
    """
    report = f"# {analysis_object.name}\n\n"
    
    if analysis_object.description:
        report += f"**Description:** {analysis_object.description}\n\n"
    
    report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    if notebook:
        
        # Get all sections and results for this notebook
        all_sections = []
        all_results = []
        
        def collect_sections_and_results(sections):
            for section in sections:
                all_sections.append(section)
                all_results.extend(section.analysis_results)
                if section.notebook_sections:
                    collect_sections_and_results(section.notebook_sections)
        
        collect_sections_and_results(notebook.notebook_sections)
        
        # Find the first element (one that's not pointed to by any other element)
        referenced_ids = set()
        for section in all_sections:
            if section.next_id:
                referenced_ids.add(section.next_id)
        for result in all_results:
            if result.next_id:
                referenced_ids.add(result.next_id)
        
        # Find first section or result that's not referenced
        first_section = next((s for s in all_sections if s.id not in referenced_ids), None)
        first_result = next((r for r in all_results if r.id not in referenced_ids), None)
        
        if first_section:
            ordered_items = build_ordered_list(all_sections, all_results, first_section.id, "notebook_section")
        elif first_result:
            ordered_items = build_ordered_list(all_sections, all_results, first_result.id, "analysis_result")
        else:
            ordered_items = []
        
        # Process the ordered items
        for item in ordered_items:
            if item["type"] == "section":
                report += await section_to_markdown(item["data"], include_code, user_id, level=2)
            elif item["type"] == "analysis_result":
                # Handle standalone analysis results (though this is unusual)
                report += await analysis_result_to_markdown(item["data"], include_code, user_id)
    
    return report


async def section_to_markdown(section: NotebookSection, include_code: bool, user_id: uuid.UUID, level: int = 1) -> str:
    """Process a notebook section and its nested sections recursively."""
    content = ""
    
    # Add section header
    header_prefix = "#" * min(level + 1, 6)  # Limit to h6
    content += f"{header_prefix} {section.section_name}\n\n"
    
    # Add section description if available
    if section.section_description:
        content += f"{section.section_description}\n\n"
    
    # Get all sections and results for this section
    child_sections = section.notebook_sections or []
    analysis_results = section.analysis_results or []
    
    # Find the first element in the chain for this section's children
    referenced_ids = set()
    for s in child_sections:
        if s.next_id:
            referenced_ids.add(s.next_id)
    for r in analysis_results:
        if r.next_id:
            referenced_ids.add(r.next_id)
    
    first_child_section = next((s for s in child_sections if s.id not in referenced_ids), None)
    first_result = next((r for r in analysis_results if r.id not in referenced_ids), None)
    
    ordered_children = []
    if first_child_section:
        ordered_children = build_ordered_list(child_sections, analysis_results, first_child_section.id, "notebook_section")
    elif first_result:
        ordered_children = build_ordered_list(child_sections, analysis_results, first_result.id, "analysis_result")
    
    # Process the ordered children
    for child in ordered_children:
        if child["type"] == "section":
            content += await section_to_markdown(child["data"], include_code, level + 1)
        elif child["type"] == "analysis_result":
            content += await analysis_result_to_markdown(child["data"], include_code, user_id)
    
    return content


async def analysis_result_to_markdown(result: AnalysisResult, include_code: bool, user_id: uuid.UUID) -> str:
    """Process an analysis result and include plots."""
    content = ""
    
    # Add analysis content
    content += f"{result.analysis}\n\n"
    
    if include_code and result.python_code:
        content += f"**Python Code:**\n```python\n{result.python_code}\n```\n\n"
    
    # Add plots for this analysis result
    from synesis_api.modules.plots.service import get_plots_by_analysis_result_id, render_plot_to_png_pyecharts
    from synesis_api.modules.data_objects.service.raw_data_service import get_aggregation_object_payload_data_by_analysis_result_id
    
    plots = await get_plots_by_analysis_result_id(result.id)
    if plots:
        # Get aggregation data for the plots
        aggregation_data = await get_aggregation_object_payload_data_by_analysis_result_id(user_id, result.id)
        for plot in plots:
            try:
                b64 = await render_plot_to_png_pyecharts(plot, aggregation_data)
                content += f"""
<div style="padding: 0 20px; box-sizing: border-box;">
<img
    src="data:image/png;base64,{b64}"
    style="width:100%; height:auto; display:block; margin: 0 auto;"
    alt="chart"
/>
</div>"""
            except Exception as e:
                print("We get an exception")
                content += f"*Error rendering plot: {str(e)}*\n\n"

    
    return content

def deep_exclude(data: Any, exclude_keys: set[str]) -> Any:
    """
    Recursively remove excluded keys from a nested dict/list structure.
    """
    if isinstance(data, dict):
        return {
            k: deep_exclude(v, exclude_keys)
            for k, v in data.items()
            if k not in exclude_keys
        }
    elif isinstance(data, list):
        return [deep_exclude(item, exclude_keys) for item in data]
    else:
        return data