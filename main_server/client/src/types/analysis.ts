import { UUID } from "crypto";

// API schemas

export interface AnalysisResult {
  id: UUID;
  analysis: string;
  pythonCode?: string | null;
  inputVariable?: string | null;
  outputVariable?: string | null;
  nextType?: "analysis_result" | "notebook_section" | null;
  nextId?: UUID | null;
  sectionId?: UUID | null;
  plotUrls: string[];
}

export interface NotebookSection {
  id: UUID;
  notebookId: UUID;
  sectionName: string;
  sectionDescription?: string | null;
  nextType?: "analysis_result" | "notebook_section" | null;
  nextId?: UUID | null;
  parentSectionId?: UUID | null;
  notebookSections: NotebookSection[];
  analysisResults: AnalysisResult[];
}

export interface Notebook {
  id: UUID;
  notebookSections: NotebookSection[];
}

export interface AnalysisInputEntities {
  datasetIds: UUID[];
  dataSourceIds: UUID[];
  modelEntityIds: UUID[];
  analysisIds: UUID[];
}

export interface AnalysisSmall {
  id: UUID;
  name: string;
  description?: string | null;
  reportGenerated: boolean;
  createdAt: string;
  inputs: AnalysisInputEntities;
}

export interface Analysis extends AnalysisSmall {
  notebook: Notebook;
  inputs: AnalysisInputEntities;
  descriptionForAgent: string;
}

export interface AnalysisStatusMessage {
  id: UUID;
  runId: UUID;
  section?: NotebookSection | null;
  analysisResult?: AnalysisResult | null;
  createdAt: string;
}

export interface GetAnalysesByIDsRequest {
  analysisIds: UUID[];
}

// DB schemas

export interface AnalysisInDB {
  id: UUID;
  name: string;
  description?: string | null;
  reportGenerated: boolean;
  createdAt: string;
  userId: UUID;
  notebookId: UUID;
}

export interface NotebookInDB {
  id: UUID;
}

export interface NotebookSectionInDB {
  id: UUID;
  notebookId: UUID;
  sectionName: string;
  sectionDescription?: string | null;
  nextType?: "analysis_result" | "notebook_section" | null;
  nextId?: UUID | null;
  parentSectionId?: UUID | null;
}

export interface AnalysisResultInDB {
  id: UUID;
  analysis: string;
  pythonCode?: string | null;
  inputVariable?: string | null;
  outputVariable?: string | null;
  nextType?: "analysis_result" | "notebook_section" | null;
  nextId?: UUID | null;
  sectionId?: UUID | null;
}

export interface DatasetInAnalysisInDB {
  analysisId: UUID;
  datasetId: UUID;
}

export interface DataSourceInAnalysisInDB {
  analysisId: UUID;
  dataSourceId: UUID;
}

export interface ModelEntityInAnalysisInDB {
  analysisId: UUID;
  modelEntityId: UUID;
}

export interface AnalysisFromPastAnalysisInDB {
  analysisId: UUID;
  pastAnalysisId: UUID;
}

// Other schemas

export interface AnalysisCreate {
  name: string;
  description?: string | null;
  inputDataSourceIds: UUID[];
  inputDatasetIds: UUID[];
  inputModelEntityIds: UUID[];
  inputAnalysisIds: UUID[];
}

export interface AnalysisResultUpdate {
  analysis?: string | null;
  pythonCode?: string | null;
}

export interface NotebookSectionCreate {
  analysisId: UUID;
  sectionName: string;
  sectionDescription?: string | null;
  parentSectionId?: UUID | null;
}

export interface NotebookSectionUpdate {
  sectionName?: string | null;
  sectionDescription?: string | null;
}

export interface GenerateReportRequest {
  filename: string;
  includeCode: boolean;
}

export interface MoveRequest {
  newSectionId?: UUID | null;
  movingElementType: "analysis_result" | "notebook_section";
  movingElementId: UUID;
  nextElementType?: "analysis_result" | "notebook_section" | null;
  nextElementId?: UUID | null;
}

export interface AnalysisResultFindRequest {
  analysisResultIds: UUID[];
}