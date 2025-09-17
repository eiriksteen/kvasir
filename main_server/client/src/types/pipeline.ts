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

export interface FunctionInputStructure {
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

export interface FunctionOutputStructure {
  id: UUID;
  position: number;
  functionId: UUID;
  structureId: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface FunctionOutputVariable {
  id: UUID;
  position: number;
  functionId: UUID;
  variableId: string;
}

export interface Function {
  id: UUID;
  name: string;
  type: "inference" | "training" | "computation";
  implementationScriptPath: string;
  setupScriptPath?: string;
  defaultConfig?: Record<string, unknown>;
  description: string;
  createdAt: string;
  updatedAt: string;
  inputStructures: FunctionInputStructure[];
  outputStructures: FunctionOutputStructure[];
  outputVariables: FunctionOutputVariable[];
}

export interface FunctionWithoutEmbedding {
  id: UUID;
  name: string;
  description: string;
  defaultConfig?: Record<string, unknown>;
  inputStructures: FunctionInputStructure[];
  outputStructures: FunctionOutputStructure[];
  outputVariables: FunctionOutputVariable[];
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

