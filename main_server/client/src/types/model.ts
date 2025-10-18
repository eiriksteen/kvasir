import { UUID } from "crypto";

export type SupportedModality = "time_series" | "tabular" | "multimodal" | "image" | "text" | "audio" | "video";
export type SupportedTask = "forecasting" | "classification" | "regression" | "clustering" | "anomaly_detection" | "generation" | "segmentation";
export type SupportedModelSource = "github" | "pypi" | "gitlab" | "huggingface" | "local";

// DB Models needed by API types

export interface ModelDefinitionInDB {
  id: UUID;
  name: string;
  modality: SupportedModality;
  task: SupportedTask;
  public: boolean;
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

export interface ModelFunctionInputObjectGroupDefinitionInDB {
  id: UUID;
  functionId: UUID;
  structureId: string;
  name: string;
  required: boolean;
  description: string;
  createdAt: string;
  updatedAt: string;
}

export interface ModelFunctionOutputObjectGroupDefinitionInDB {
  id: UUID;
  functionId: UUID;
  name?: string | null;
  structureId: string;
  description: string;
  createdAt: string;
  updatedAt: string;
}

export interface ModelEntityInDB {
  id: UUID;
  name: string;
  userId: UUID;
  description: string;
  modelId: UUID;
  config: Record<string, unknown>;
  weightsSaveDir?: string | null;
  pipelineId?: UUID | null;
  createdAt: string;
  updatedAt: string;
}

// API Models

export interface ModelFunctionFull extends ModelFunctionInDB {
  inputObjectGroups: ModelFunctionInputObjectGroupDefinitionInDB[];
  outputObjectGroups: ModelFunctionOutputObjectGroupDefinitionInDB[];
}

export interface ModelFull {
  id: UUID;
  definitionId: UUID;
  version: number;
  filename: string;
  modulePath: string;
  pythonClassName: string;
  description: string;
  newestUpdateDescription: string;
  userId: UUID;
  sourceId: UUID;
  programmingLanguageWithVersion: string;
  implementationScriptPath: string;
  setupScriptPath?: string | null;
  modelClassDocstring: string;
  trainingFunctionId: UUID;
  inferenceFunctionId: UUID;
  defaultConfig: Record<string, unknown>;
  configSchema: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
  definition: ModelDefinitionInDB;
  trainingFunction: ModelFunctionFull;
  inferenceFunction: ModelFunctionFull;
}

export interface ModelEntityWithModelDef extends ModelEntityInDB {
  model: ModelFull;
}

// Type aliases for usage in components
export type Model = ModelFull;
export type ModelEntity = ModelEntityWithModelDef;


export interface ModelSourceBase {
  id: UUID;
  user_id: string;
  type: SupportedModelSource;
  name: string;
  createdAt: string;
  updatedAt: string;
}

export interface PypiModelSource extends ModelSourceBase {
  type: "pypi";
  packageName: string;
  packageVersion: string;
}

export type ModelSource = PypiModelSource // | GithubModelSource | GitlabModelSource | HuggingfaceModelSource | LocalModelSource;