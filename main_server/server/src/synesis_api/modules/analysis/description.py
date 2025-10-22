from synesis_schemas.main_server import NotebookSection, Notebook, AnalysisSmall, AnalysisInputEntities


def get_analysis_description(
    analysis_small: AnalysisSmall,
    notebook: Notebook,
    # inputs: AnalysisInputEntities
) -> str:
    lines = [
        f"The following is a textual representation of the analysis object with name {analysis_small.name} and id {analysis_small.id}:<<<",
        f"Analysis object: {analysis_small.name}",
        f"Analysis object description: {analysis_small.description}",
        f"Each analysis object has an associated notebook structure with sections, subsections and analysis results.",
        f"The following is a textual representation of the notebook:",
    ]

    for section in notebook.notebook_sections:
        lines.extend(_get_section_description(section))

    lines.append(">>>")

    return "\n".join(lines)


def _get_section_description(section: NotebookSection) -> str:
    lines = []
    lines.append(f"Section: {section.section_name}")
    lines.append(f"Section id: {section.id}")
    if section.section_description:
        lines.append(f"Section description: {section.section_description}")
        if section.parent_section_id:
            lines.append(
                f"This section is a subsection of the section with id: {section.parent_section_id}")

    if len(section.analysis_results) > 0:
        lines.append(
            f"The following analysis results belong to the section with id {section.id}:")
    for i, analysis_result in enumerate(section.analysis_results):
        lines.append(f"Analysis result {i+1}: [")
        lines.append(f"Analysis result id: {analysis_result.id}")
        lines.append(f"Analysis result: {analysis_result.analysis}")
        lines.append(
            f"The result was from this code: {analysis_result.python_code}")
        lines.append("]")

    for subsection in section.notebook_sections:
        lines.extend(_get_section_description(subsection))

    return lines
