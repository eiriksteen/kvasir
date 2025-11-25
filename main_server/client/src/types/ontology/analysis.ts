import { UUID } from "crypto";
import { ImageBase, ImageCreate, EchartBase, EchartCreate, TableBase, TableCreate } from "./visualization";

// Base Models

export interface AnalysisBase {
  id: UUID;
  name: string;
  description?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface AnalysisSectionBase {
  id: UUID;
  name: string;
  analysisId: UUID;
  description?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface AnalysisCellBase {
  id: UUID;
  order: number;
  type: "markdown" | "code";
  sectionId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface MarkdownCellBase {
  id: UUID; // Foreign key to AnalysisCellBase.id
  markdown: string;
  createdAt: string;
  updatedAt: string;
}

export interface CodeCellBase {
  id: UUID; // Foreign key to AnalysisCellBase.id
  code: string;
  createdAt: string;
  updatedAt: string;
}

export interface CodeOutputBase {
  id: UUID; // Foreign key to CodeCellBase.id
  output: string;
  createdAt: string;
  updatedAt: string;
}

export interface ResultImageBase {
  id: UUID;
  codeCellId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface ResultEChartBase {
  id: UUID;
  codeCellId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface ResultTableBase {
  id: UUID;
  codeCellId: UUID;
  createdAt: string;
  updatedAt: string;
}

// Composite Models

export interface CodeOutput extends CodeOutputBase {
  images: ImageBase[];
  echarts: EchartBase[];
  tables: TableBase[];
}

export interface CodeCell extends CodeCellBase {
  output?: CodeOutput | null;
}

export interface AnalysisCell extends AnalysisCellBase {
  typeFields: CodeCell | MarkdownCellBase;
}

export interface Section extends AnalysisSectionBase {
  cells: AnalysisCell[];
}

export interface Analysis extends AnalysisBase {
  sections: Section[];
}

// Create Models

export interface CodeOutputCreate {
  codeCellId?: UUID | null;
  output: string;
  images?: ImageCreate[] | null;
  echarts?: EchartCreate[] | null;
  tables?: TableCreate[] | null;
}

export interface CodeCellCreate {
  sectionId: UUID;
  code: string;
  order: number;
  output?: CodeOutputCreate | null;
}

export interface MarkdownCellCreate {
  sectionId: UUID;
  markdown: string;
  order: number;
}

export interface SectionCreate {
  analysisId: UUID;
  name: string;
  description?: string | null;
  codeCellsCreate?: CodeCellCreate[] | null;
  markdownCellsCreate?: MarkdownCellCreate[] | null;
}

export interface AnalysisCreate {
  name: string;
  description?: string | null;
  sectionsCreate?: SectionCreate[] | null;
}

