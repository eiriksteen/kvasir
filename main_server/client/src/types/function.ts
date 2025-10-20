import { UUID } from "crypto";
import { ScriptInDB } from "./code";

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

export interface FunctionInputObjectGroupDefinitionInDB {
  id: UUID;
  functionId: UUID;
  structureId: string;
  name: string;
  required: boolean;
  description: string;
  createdAt: string;
  updatedAt: string;
}

export interface FunctionOutputObjectGroupDefinitionInDB {
  id: UUID;
  functionId: UUID;
  name: string;
  structureId: string;
  outputEntityIdName: string;
  description: string;
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
  implementationScriptId: UUID;
  setupScriptId?: UUID | null;
  docstring: string;
  description: string;
  createdAt: string;
  updatedAt: string;
}

export interface Function extends FunctionWithoutEmbedding {
  definition: FunctionDefinitionInDB;
  inputObjectGroups: FunctionInputObjectGroupDefinitionInDB[];
  outputObjectGroups: FunctionOutputObjectGroupDefinitionInDB[];
  implementationScript: ScriptInDB;
  setupScript?: ScriptInDB | null;
  descriptionForAgent: string;
}
