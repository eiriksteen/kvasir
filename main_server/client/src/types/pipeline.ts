import { UUID } from "crypto";
import { FunctionWithoutEmbedding } from "./function";

// DB Models

export interface PipelineInDB {
  id: UUID;
  userId: UUID;
  name: string;
  description: string;
  createdAt: string;
  updatedAt: string;
}

export interface PipelineImplementationInDB {
  id: UUID;
  pythonFunctionName: string;
  docstring: string;
  description: string;
  argsSchema: Record<string, unknown>;
  outputVariablesSchema: Record<string, unknown>;
  implementationScriptPath: string;
  createdAt: string;
  updatedAt: string;
}

export interface DataSourceInPipelineInDB {
  dataSourceId: UUID;
  pipelineId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface DatasetInPipelineInDB {
  datasetId: UUID;
  pipelineId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface ModelEntityInPipelineInDB {
  modelEntityId: UUID;
  pipelineId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface AnalysisInPipelineInDB {
  analysisId: UUID;
  pipelineId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface FunctionInPipelineInDB {
  pipelineId: UUID;
  functionId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface PipelineRunInDB {
  id: UUID;
  pipelineId: UUID;
  status: "running" | "completed" | "failed";
  args: Record<string, unknown>;
  outputVariables: Record<string, unknown>;
  startTime: string;
  endTime?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface PipelineOutputDatasetInDB {
  pipelineId: UUID;
  datasetId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface PipelineOutputModelEntityInDB {
  pipelineId: UUID;
  modelEntityId: UUID;
  createdAt: string;
  updatedAt: string;
}

// API Models

export interface PipelineInputEntities {
  dataSourceIds: UUID[];
  datasetIds: UUID[];
  modelEntityIds: UUID[];
  analysisIds: UUID[];
}

export interface PipelineOutputEntities {
  datasetIds: UUID[];
  modelEntityIds: UUID[];
}

export interface PipelineImplementation extends PipelineImplementationInDB {
  functions: FunctionWithoutEmbedding[];
  implementationScriptPath: string;
  runs: PipelineRunInDB[];
}

export interface Pipeline extends PipelineInDB {
  inputs: PipelineInputEntities;
  outputs: PipelineOutputEntities;
  implementation?: PipelineImplementation | null;
  descriptionForAgent: string;
}

export interface PipelineRunStatusUpdate {
  status: "running" | "completed" | "failed";
}

export interface PipelineRunDatasetOutputCreate {
  datasetId: UUID;
}

export interface PipelineRunModelEntityOutputCreate {
  modelEntityId: UUID;
}

// Create Models

export interface PipelineCreate {
  name: string;
  description?: string | null;
  inputDataSourceIds: UUID[];
  inputDatasetIds: UUID[];
  inputModelEntityIds: UUID[];
  inputAnalysisIds: UUID[];
}

export interface PipelineImplementationCreate {
  pythonFunctionName: string;
  docstring: string;
  description: string;
  argsSchema: Record<string, unknown>;
  defaultArgs: Record<string, unknown>;
  outputVariablesSchema: Record<string, unknown>;
  functionIds: UUID[];
  implementationScriptPath: string;
  pipelineId?: UUID | null;
  pipelineCreate?: PipelineCreate | null;
}

export interface RunPipelineRequest {
  args: Record<string, unknown>;
  projectId: UUID;
  pipelineId: UUID;
  conversationId?: UUID | null;
  runId?: UUID | null;
}

export interface GetPipelinesByIDsRequest {
  pipelineIds: UUID[];
}

export interface PipelineRunOutputVariablesUpdate {
  pipelineRunId: UUID;
  newOutputVariables: Record<string, unknown>;
}
