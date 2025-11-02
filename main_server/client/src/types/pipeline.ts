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
  defaultArgs: Record<string, unknown>;
  outputVariablesSchema: Record<string, unknown>;
  implementationScriptPath: string;
  createdAt: string;
  updatedAt: string;
}

export interface DataSourceSupportedInPipelineInDB {
  dataSourceId: UUID;
  pipelineId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface DatasetSupportedInPipelineInDB {
  datasetId: UUID;
  pipelineId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface ModelEntitySupportedInPipelineInDB {
  modelEntityId: UUID;
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
  name?: string | null;
  description?: string | null;
  status: "running" | "completed" | "failed";
  args: Record<string, unknown>;
  outputVariables: Record<string, unknown>;
  startTime: string;
  endTime?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface DatasetInPipelineRunInDB {
  pipelineRunId: UUID;
  datasetId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface DataSourceInPipelineRunInDB {
  pipelineRunId: UUID;
  dataSourceId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface ModelEntityInPipelineRunInDB {
  pipelineRunId: UUID;
  modelEntityId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface PipelineRunOutputDatasetInDB {
  pipelineRunId: UUID;
  datasetId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface PipelineRunOutputModelEntityInDB {
  pipelineRunId: UUID;
  modelEntityId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface PipelineRunOutputDataSourceInDB {
  pipelineRunId: UUID;
  dataSourceId: UUID;
  createdAt: string;
  updatedAt: string;
}

// API Models

export interface PipelineRunEntities {
  dataSourceIds: UUID[];
  datasetIds: UUID[];
  modelEntityIds: UUID[];
}

export interface PipelineRun extends PipelineRunInDB {
  inputs: PipelineRunEntities;
  outputs: PipelineRunEntities;
}

export interface PipelineImplementation extends PipelineImplementationInDB {
  functions: FunctionWithoutEmbedding[];
  implementationScriptPath: string;
}

export interface Pipeline extends PipelineInDB {
  supportedInputs: PipelineRunEntities;
  runs: PipelineRun[];
  implementation?: PipelineImplementation | null;
  descriptionForAgent: string;
}

export interface PipelineRunStatusUpdate {
  status: "running" | "completed" | "failed";
}

export interface PipelineRunOutputsCreate {
  datasetIds: UUID[];
  modelEntityIds: UUID[];
  dataSourceIds: UUID[];
}

// Create Models

export interface PipelineCreate {
  name: string;
  description?: string | null;
  supportedInputs: PipelineRunEntities;
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
  projectId: UUID;
  pipelineId: UUID;
  args: Record<string, unknown>;
  inputs: PipelineRunEntities;
  name?: string | null;
  description?: string | null;
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
