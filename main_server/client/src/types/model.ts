import { UUID } from "crypto";
import { FunctionWithoutEmbedding } from "./function";


export interface Model {
  id: UUID;
  name: string;
  description: string;
  ownerId: UUID;
  public: boolean;
  modality: string;
  sourceId: UUID;
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
  name: string;
  description: string;
  modelId: UUID;
  projectId: UUID;
  weightsSaveDir?: string;
  pipelineId?: UUID;
  config?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
  model: Model;
}