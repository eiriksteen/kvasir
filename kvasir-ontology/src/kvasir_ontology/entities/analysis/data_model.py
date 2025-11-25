from uuid import UUID
from datetime import datetime
from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field


from kvasir_ontology.visualization.data_model import ImageCreate, EchartCreate, TableCreate, ImageBase, EchartBase, TableBase


class AnalysisBase(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AnalysisSectionBase(BaseModel):
    id: UUID
    name: str
    analysis_id: UUID
    order: int
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AnalysisCellBase(BaseModel):
    id: UUID
    order: int
    type: Literal["markdown", "code"]
    section_id: UUID
    created_at: datetime
    updated_at: datetime


class MarkdownCellBase(BaseModel):
    id: UUID  # Foreign key to AnalysisCellBase.id
    markdown: str
    created_at: datetime
    updated_at: datetime


class CodeCellBase(BaseModel):
    id: UUID  # Foreign key to AnalysisItemBase.id
    code: str
    created_at: datetime
    updated_at: datetime


class CodeOutputBase(BaseModel):
    id: UUID  # Foreign key to CodeCellBase.id
    output: str
    created_at: datetime
    updated_at: datetime


class ResultImageBase(BaseModel):
    id: UUID
    code_cell_id: UUID
    created_at: datetime
    updated_at: datetime


class ResultEChartBase(BaseModel):
    id: UUID
    code_cell_id: UUID
    created_at: datetime
    updated_at: datetime


class ResultTableBase(BaseModel):
    id: UUID
    code_cell_id: UUID
    created_at: datetime
    updated_at: datetime

##


class CodeOutput(CodeOutputBase):
    images: List[ImageBase] = Field(default_factory=list)
    echarts: List[EchartBase] = Field(default_factory=list)
    tables: List[TableBase] = Field(default_factory=list)


class CodeCell(CodeCellBase):
    output: Optional[CodeOutput] = None


class AnalysisCell(AnalysisCellBase):
    type_fields: Union[CodeCell, MarkdownCellBase]


class Section(AnalysisSectionBase):
    cells: List[AnalysisCell] = Field(default_factory=list)


class Analysis(AnalysisBase):
    sections: List[Section] = Field(default_factory=list)


##


class CodeOutputCreate(BaseModel):
    code_cell_id: Optional[UUID] = None
    output: str
    images: Optional[List[ImageCreate]] = None
    echarts: Optional[List[EchartCreate]] = None
    tables: Optional[List[TableCreate]] = None


class CodeCellCreate(BaseModel):
    section_id: UUID
    code: str
    order: Optional[int] = None
    output: Optional[CodeOutputCreate] = None


class MarkdownCellCreate(BaseModel):
    section_id: UUID
    markdown: str
    order: Optional[int] = None


class SectionCreate(BaseModel):
    analysis_id: UUID
    name: Optional[str] = None
    order: Optional[int] = None
    description: Optional[str] = None
    code_cells_create: Optional[List[CodeCellCreate]] = None
    markdown_cells_create: Optional[List[MarkdownCellCreate]] = None


class AnalysisCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sections_create: Optional[List[SectionCreate]] = None
