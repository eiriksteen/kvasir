import { UUID } from "crypto";


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
