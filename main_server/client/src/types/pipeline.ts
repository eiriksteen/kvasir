import { UUID } from "crypto";
import { FunctionWithoutEmbedding } from "./function";
import { ScriptInDB } from "./code";

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
  args: Record<string, unknown>;
  argsSchema: Record<string, unknown>;
  outputVariablesSchema: Record<string, unknown>;
  implementationScriptId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface PipelineRunInDB {
  id: UUID;
  pipelineId: UUID;
  status: "running" | "completed" | "failed";
  startTime: string;
  endTime: string | null;
  createdAt: string;
  updatedAt: string;
}

// API Models

export interface PipelineInputEntities {
  dataSourceIds: UUID[];
  datasetIds: UUID[];
  modelEntityIds: UUID[];
}

export interface PipelineOutputEntities {
  datasetIds: UUID[];
  modelEntityIds: UUID[];
}

export interface PipelineImplementation extends PipelineImplementationInDB {
  functions: FunctionWithoutEmbedding[];
  implementationScript: ScriptInDB;
  runs: PipelineRunInDB[];
}

export interface Pipeline extends PipelineInDB {
  inputs: PipelineInputEntities;
  outputs: PipelineOutputEntities;
  implementation: PipelineImplementation | null;
}
