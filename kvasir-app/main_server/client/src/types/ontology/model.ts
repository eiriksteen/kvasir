import { UUID } from "crypto";

// Supported Types

export type SupportedModality = 
  | "time_series"
  | "tabular"
  | "multimodal"
  | "image"
  | "text"
  | "audio"
  | "video";

export type SupportedTask = 
  | "forecasting"
  | "classification"
  | "regression"
  | "clustering"
  | "anomaly_detection"
  | "generation"
  | "segmentation";

export type FunctionType = "training" | "inference";

export type SupportedModelSource = "github" | "pypi";

// Base Models

export interface ModelBase {
  id: UUID;
  name: string;
  userId: UUID;
  description: string;
  createdAt: string;
  updatedAt: string;
}

export interface ModelImplementationBase {
  id: UUID; // Foreign key to model.id
  modality: SupportedModality;
  task: SupportedTask;
  public: boolean;
  pythonClassName: string;
  description: string;
  userId: UUID;
  source: SupportedModelSource;
  trainingFunctionId: UUID;
  inferenceFunctionId: UUID;
  implementationScriptPath: string;
  modelClassDocstring: string;
  defaultConfig: Record<string, unknown>;
  configSchema: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface ModelFunctionBase {
  id: UUID;
  docstring: string;
  argsSchema: Record<string, unknown>;
  defaultArgs: Record<string, unknown>;
  outputVariablesSchema: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface ModelInstantiatedBase {
  id: UUID;
  modelId: UUID;
  name: string;
  userId: UUID;
  description: string;
  config: Record<string, unknown>;
  weightsSaveDir?: string | null;
  createdAt: string;
  updatedAt: string;
}

// Composite Models

export interface ModelImplementation extends ModelImplementationBase {
  trainingFunction: ModelFunctionBase;
  inferenceFunction: ModelFunctionBase;
  implementationScriptPath: string;
}

export interface Model extends ModelBase {
  // None until implementation added (allows immediate UI update)
  implementation?: ModelImplementation | null;
}

export interface ModelInstantiated extends ModelInstantiatedBase {
  model: Model;
}

// Create Models

export interface ModelFunctionCreate {
  docstring: string;
  argsSchema: Record<string, unknown>;
  defaultArgs: Record<string, unknown>;
  outputVariablesSchema: Record<string, unknown>;
}

export interface ModelImplementationCreate {
  pythonClassName: string;
  public: boolean;
  modality: SupportedModality;
  task: SupportedTask;
  source: SupportedModelSource;
  modelClassDocstring: string;
  trainingFunction: ModelFunctionCreate;
  inferenceFunction: ModelFunctionCreate;
  defaultConfig: Record<string, unknown>;
  configSchema: Record<string, unknown>;
  implementationScriptPath: string;
  modelId: UUID;
}

export interface ModelCreate {
  name: string;
  userId: UUID;
  description: string;
  implementationCreate?: ModelImplementationCreate | null;
}

export interface ModelInstantiatedCreate {
  name: string;
  description: string;
  config: Record<string, unknown>;
  weightsSaveDir?: string | null;
  pipelineId?: UUID | null;
  modelCreate?: ModelCreate | null;
  modelId?: UUID | null;
}

