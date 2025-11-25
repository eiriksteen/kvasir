import { UUID } from "crypto";

export type PipelineRunStatus = "running" | "completed" | "failed";

// Base Models

export interface PipelineBase {
  id: UUID;
  userId: UUID;
  name: string;
  description: string;
  createdAt: string;
  updatedAt: string;
}

export interface PipelineImplementationBase {
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

export interface PipelineRunBase {
  id: UUID;
  args: Record<string, unknown>;
  pipelineId: UUID;
  outputVariables: Record<string, unknown>;
  name?: string | null;
  description?: string | null;
  status: PipelineRunStatus;
  startTime: string;
  endTime?: string | null;
  createdAt: string;
  updatedAt: string;
}

// Composite Models

export interface Pipeline extends PipelineBase {
  runs: PipelineRunBase[];
  implementation?: PipelineImplementationBase | null;
}

// Create Models

export interface PipelineImplementationCreate {
  pythonFunctionName: string;
  docstring: string;
  description: string;
  argsSchema: Record<string, unknown>;
  defaultArgs: Record<string, unknown>;
  outputVariablesSchema: Record<string, unknown>;
  implementationScriptPath: string;
  pipelineId: UUID;
}

export interface PipelineRunCreate {
  name: string;
  args: Record<string, unknown>;
  pipelineId: UUID;
  outputVariables?: Record<string, unknown>;
  description?: string | null;
  status?: PipelineRunStatus;
}

export interface PipelineCreate {
  name: string;
  description?: string | null;
  implementationCreate?: PipelineImplementationCreate | null;
  runsCreate?: PipelineRunCreate[] | null;
}

