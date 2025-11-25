from uuid import UUID
from typing import List, AsyncGenerator, Union
from abc import ABC, abstractmethod

from kvasir_ontology.entities.analysis.data_model import Analysis, AnalysisCreate, SectionCreate, CodeCellCreate, MarkdownCellCreate, CodeOutputCreate, Section, AnalysisCell
from kvasir_ontology.visualization.data_model import ImageCreate, EchartCreate, TableCreate


class AnalysisInterface(ABC):

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    @abstractmethod
    async def create_analysis(self, analysis: AnalysisCreate) -> Analysis:
        pass

    @abstractmethod
    async def get_analysis(self, analysis_id: UUID) -> Analysis:
        pass

    @abstractmethod
    async def get_analyses(self, analysis_ids: List[UUID]) -> List[Analysis]:
        pass

    @abstractmethod
    async def create_section(self, section: SectionCreate) -> Section:
        pass

    @abstractmethod
    async def create_markdown_cell(self, markdown_cell: MarkdownCellCreate) -> AnalysisCell:
        pass

    @abstractmethod
    async def create_code_cell(self, code_cell: CodeCellCreate) -> AnalysisCell:
        pass

    @abstractmethod
    async def create_code_output(self, code_output: CodeOutputCreate) -> Analysis:
        pass

    @abstractmethod
    async def create_code_output_image(self, code_cell_id: UUID, code_output_image: ImageCreate) -> Analysis:
        pass

    @abstractmethod
    async def create_code_output_echart(self, code_cell_id: UUID, code_output_echart: EchartCreate) -> Analysis:
        pass

    @abstractmethod
    async def create_code_output_table(self, code_cell_id: UUID, code_output_table: TableCreate) -> Analysis:
        pass

    @abstractmethod
    async def delete_analysis(self, analysis_id: UUID) -> None:
        pass

    @abstractmethod
    async def delete_cells(self, cell_ids: List[UUID]) -> None:
        pass

    @abstractmethod
    async def delete_sections(self, section_ids: List[UUID]) -> None:
        pass

    @abstractmethod
    async def write_to_analysis_stream(self, run_id: UUID, message: Union[Section, AnalysisCell]) -> None:
        pass

    @abstractmethod
    async def listen_to_analysis_stream(self, run_id: UUID) -> AsyncGenerator[Union[Section, AnalysisCell], None]:
        pass
