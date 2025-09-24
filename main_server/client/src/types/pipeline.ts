import { UUID } from "crypto";
import { FunctionWithoutEmbedding } from "./function";

// API Models (matching schema.py API schemas)


export interface PipelineSources {
  datasetIds: UUID[];
  modelEntityIds: UUID[];
}

export interface Pipeline {
  id: UUID;
  userId: UUID;
  name: string;
  schedule: "periodic" | "on_demand" | "on_event";
  cronSchedule?: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  sources: PipelineSources;
}

export interface FunctionInPipeline {
  id: UUID;
  pipelineId: UUID;
  functionId: UUID;
  position: number;
  config?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface PipelineWithFunctions extends Pipeline {
  functions: FunctionWithoutEmbedding[];
}

