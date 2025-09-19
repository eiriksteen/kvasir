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

export interface Model {
  id: UUID;
  name: string;
  description: string;
  ownerId: UUID;
  public: boolean;
  modality: string;
  source: string;
  programmingLanguageWithVersion: string;
  setupScriptPath?: string;
  defaultConfig?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
  inferenceFunctionId: UUID;
  trainingFunctionId: UUID;
  task: string;
  embedding: number[];
  inferenceFunction: FunctionWithoutEmbedding;
  trainingFunction: FunctionWithoutEmbedding;
}


export interface ModelEntity {
  id: UUID;
  modelId: UUID;
  projectId: UUID;
  weightsSaveDir?: string;
  config?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}



