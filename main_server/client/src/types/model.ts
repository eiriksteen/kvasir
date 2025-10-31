import { UUID } from "crypto";

export type SupportedModality = "time_series" | "tabular" | "multimodal" | "image" | "text" | "audio" | "video";
export type SupportedTask = "forecasting" | "classification" | "regression" | "clustering" | "anomaly_detection" | "generation" | "segmentation";
export type FunctionType = "training" | "inference";
export type SupportedModelSource = "github" | "pypi";

// DB Models

export interface ModelDefinitionInDB {
  id: UUID;
  name: string;
  modality: SupportedModality;
  task: SupportedTask;
  public: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface ModelImplementationInDB {
  id: UUID;
  definitionId: UUID;
  version: number;
  pythonClassName: string;
  description: string;
  newestUpdateDescription: string;
  userId: UUID;
  sourceId: UUID;
  embedding: number[];
  implementationScriptPath: string;
  setupScriptPath?: string | null;
  modelClassDocstring: string;
  defaultConfig: Record<string, unknown>;
  configSchema: Record<string, unknown>;
  trainingFunctionId: UUID;
  inferenceFunctionId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface ModelEntityInDB {
  id: UUID;
  name: string;
  userId: UUID;
  description: string;
}

export interface ModelEntityImplementationInDB {
  id: UUID;
  modelId: UUID;
  config: Record<string, unknown>;
  weightsSaveDir?: string | null;
  pipelineId?: UUID | null;
  createdAt: string;
  updatedAt: string;
}

export interface ModelFunctionInDB {
  id: UUID;
  docstring: string;
  argsSchema: Record<string, unknown>;
  defaultArgs: Record<string, unknown>;
  outputVariablesSchema: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface ModelEntityFromPipelineInDB {
  pipelineId: UUID;
  modelEntityId: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface ModelSourceInDB {
  id: UUID;
  type: SupportedModelSource;
  name: string;
  description: string;
  createdAt: string;
  updatedAt: string;
}

export interface PypiModelSourceInDB {
  id: UUID;
  packageName: string;
  packageVersion: string;
  createdAt: string;
  updatedAt: string;
}

// API Models

export interface ModelImplementationWithoutEmbedding {
  id: UUID;
  definitionId: UUID;
  version: number;
  pythonClassName: string;
  description: string;
  newestUpdateDescription: string;
  userId: UUID;
  sourceId: UUID;
  modelClassDocstring: string;
  trainingFunctionId: UUID;
  inferenceFunctionId: UUID;
  defaultConfig: Record<string, unknown>;
  configSchema: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface ModelImplementation extends ModelImplementationWithoutEmbedding {
  definition: ModelDefinitionInDB;
  trainingFunction: ModelFunctionInDB;
  inferenceFunction: ModelFunctionInDB;
  implementationScriptPath: string;
  setupScriptPath?: string | null;
  descriptionForAgent: string;
}

export interface ModelEntityImplementation extends ModelEntityImplementationInDB {
  modelImplementation: ModelImplementation;
}

export interface ModelEntity extends ModelEntityInDB {
  implementation?: ModelEntityImplementation | null;
  descriptionForAgent: string;
}

export interface GetModelEntityByIDsRequest {
  modelEntityIds: UUID[];
}

export interface ModelSource extends ModelSourceInDB {
  typeFields: PypiModelSourceInDB; // TODO: Add github when implemented
}

// Create Models

export interface ModelFunctionCreate {
  docstring: string;
  argsSchema: Record<string, unknown>;
  defaultArgs: Record<string, unknown>;
  outputVariablesSchema: Record<string, unknown>;
}

export interface PypiModelSourceCreate {
  packageName: string;
  packageVersion: string;
  type: "pypi";
}

export interface ModelSourceCreate {
  type: SupportedModelSource;
  description: string;
  name: string;
  typeFields: PypiModelSourceCreate; // TODO: Add github when implemented
}

export interface ModelImplementationCreate {
  name: string;
  pythonClassName: string;
  public: boolean;
  description: string;
  modality: SupportedModality;
  task: SupportedTask;
  source: ModelSourceCreate;
  modelClassDocstring: string;
  trainingFunction: ModelFunctionCreate;
  inferenceFunction: ModelFunctionCreate;
  defaultConfig: Record<string, unknown>;
  configSchema: Record<string, unknown>;
  implementationScriptPath: string;
  setupScriptPath?: string | null;
}

export interface ModelEntityCreate {
  name: string;
  description: string;
}

export interface ModelEntityImplementationCreate {
  config: Record<string, unknown>;
  weightsSaveDir?: string | null;
  pipelineId?: UUID | null;
  modelImplementationId?: UUID | null;
  modelImplementationCreate?: ModelImplementationCreate | null;
  modelEntityId?: UUID | null;
  modelEntityCreate?: ModelEntityCreate | null;
}

// Update Models

export interface ModelFunctionUpdateCreate {
  docstring?: string | null;
  argsSchema?: Record<string, unknown> | null;
  outputVariablesSchema?: Record<string, unknown> | null;
  defaultArgs?: Record<string, unknown> | null;
}

export interface ModelUpdateCreate {
  definitionId: UUID;
  updatesMadeDescription: string;
  newImplementationScriptPath: string;
  updatedDescription?: string | null;
  updatedPythonClassName?: string | null;
  updatedModelClassDocstring?: string | null;
  updatedDefaultConfig?: Record<string, unknown> | null;
  updatedTrainingFunction?: ModelFunctionUpdateCreate | null;
  updatedInferenceFunction?: ModelFunctionUpdateCreate | null;
  updatedConfigSchema?: Record<string, unknown> | null;
  modelEntitiesToUpdate?: UUID[] | null;
  newSetupScriptPath?: string | null;
}

export interface ModelEntityConfigUpdate {
  config: Record<string, unknown>;
}

// Type aliases for usage in components
export type Model = ModelImplementation;