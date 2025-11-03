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

// API Models

export interface PipelineImplementation extends PipelineImplementationInDB {
  functions: FunctionWithoutEmbedding[];
  implementationScriptPath: string;
}

export interface Pipeline extends PipelineInDB {
  runs: PipelineRunInDB[];
  implementation?: PipelineImplementation | null;
}

export interface PipelineRunStatusUpdate {
  status: "running" | "completed" | "failed";
}

// Pipeline run outputs are managed through entity graph

// Create Models

export interface PipelineCreate {
  name: string;
  description?: string | null;
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
