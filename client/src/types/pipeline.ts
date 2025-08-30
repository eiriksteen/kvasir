import { UUID } from "crypto";

// API Models (matching schema.py API schemas)

export interface Pipeline {
  id: UUID;
  userId: UUID;
  name: string;
  schedule: "periodic" | "on_demand" | "on_event";
  cronSchedule?: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface FunctionInput {
  id: UUID;
  position: number;
  functionId: UUID;
  structureId: string;
  name: string;
  required: boolean;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface FunctionOutput {
  id: UUID;
  position: number;
  functionId: UUID;
  structureId: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Function {
  id: UUID;
  name: string;
  implementationScriptPath: string;
  setupScriptPath?: string;
  configScriptPath?: string;
  description: string;
  defaultConfig?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
  inputs: FunctionInput[];
  outputs: FunctionOutput[];
}

export interface FunctionWithoutEmbedding {
  id: UUID;
  name: string;
  implementationScriptPath: string;
  setupScriptPath: string;
  description: string;
  defaultConfig?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
  inputs: FunctionInput[];
  outputs: FunctionOutput[];
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

export interface Modality {
  id: UUID;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Task {
  id: UUID;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Source {
  id: UUID;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ProgrammingLanguage {
  id: UUID;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ProgrammingLanguageVersion {
  id: UUID;
  programmingLanguageId: UUID;
  version: string;
  createdAt: string;
  updatedAt: string;
}

export interface Model {
  id: UUID;
  name: string;
  description: string;
  ownerId: UUID;
  public: boolean;
  modalityId: UUID;
  sourceId: UUID;
  programmingLanguageVersionId: UUID;
  setupScriptPath: string;
  configScriptPath: string;
  inputDescription: string;
  outputDescription: string;
  configParameters: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface ModelTask {
  id: UUID;
  modelId: UUID;
  taskId: UUID;
  inferenceScriptPath: string;
  trainingScriptPath: string;
  inferenceFunctionId: UUID;
  trainingFunctionId: UUID;
  createdAt: string;
  updatedAt: string;
}

// Create schemas (matching schema.py Create schemas)

export interface FunctionInputCreate {
  structureId: string;
  name: string;
  description: string;
  required: boolean;
}

export interface FunctionOutputCreate {
  structureId: string;
  name: string;
  description: string;
}