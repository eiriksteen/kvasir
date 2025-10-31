import { UUID } from "crypto";

export type FunctionType = "inference" | "training" | "computation" | "tool";

// DB Models

export interface FunctionDefinitionInDB {
  id: UUID;
  name: string;
  type: FunctionType;
  argsDataclassName: string;
  inputDataclassName: string;
  outputDataclassName: string;
  outputVariablesDataclassName: string;
  createdAt: string;
  updatedAt: string;
}

export interface FunctionInDB {
  id: UUID;
  version: number;
  pythonFunctionName: string;
  definitionId: UUID;
  defaultArgs: Record<string, unknown>;
  argsSchema: Record<string, unknown>;
  outputVariablesSchema: Record<string, unknown>;
  newestUpdateDescription: string;
  implementationScriptPath: string;
  setupScriptPath?: string | null;
  docstring: string;
  description: string;
  embedding: number[];
  createdAt: string;
  updatedAt: string;
}

// API Models

export interface FunctionWithoutEmbedding {
  id: UUID;
  definitionId: UUID;
  version: number;
  argsSchema: Record<string, unknown>;
  defaultArgs: Record<string, unknown>;
  outputVariablesSchema: Record<string, unknown>;
  newestUpdateDescription: string;
  pythonFunctionName: string;
  implementationScriptPath: string;
  setupScriptPath?: string | null;
  docstring: string;
  description: string;
  createdAt: string;
  updatedAt: string;
}

export interface Function extends FunctionWithoutEmbedding {
  definition: FunctionDefinitionInDB;
  implementationScriptPath: string;
  setupScriptPath?: string | null;
  descriptionForAgent: string;
}

export interface GetFunctionsRequest {
  functionIds: UUID[];
}

// Create Models

export interface FunctionCreate {
  name: string;
  pythonFunctionName: string;
  docstring: string;
  description: string;
  argsSchema: Record<string, unknown>;
  defaultArgs: Record<string, unknown>;
  outputVariablesSchema: Record<string, unknown>;
  type: FunctionType;
  argsDataclassName: string;
  inputDataclassName: string;
  outputDataclassName: string;
  outputVariablesDataclassName: string;
  implementationScriptPath: string;
  setupScriptPath?: string | null;
}

export interface FunctionUpdateCreate {
  definitionId: UUID;
  updatesMadeDescription: string;
  newImplementationScriptPath: string;
  newSetupScriptPath?: string | null;
  updatedPythonFunctionName?: string | null;
  updatedDescription?: string | null;
  updatedDocstring?: string | null;
  updatedDefaultArgs?: Record<string, unknown> | null;
  updatedArgsSchema?: Record<string, unknown> | null;
  updatedOutputVariablesSchema?: Record<string, unknown> | null;
}
