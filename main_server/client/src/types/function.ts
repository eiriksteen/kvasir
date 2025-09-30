import { UUID } from "crypto";


export interface FunctionInputObjectGroupDesc {
  id: UUID;
  functionId: UUID;
  structureId: string;
  name: string;
  required: boolean;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface FunctionOutputObjectGroupDesc {
  id: UUID;
  functionId: UUID;
  structureId: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface FunctionOutputVariableDesc {
  id: UUID;
  functionId: UUID;
  variableId: string;
}

export interface Function {
  id: UUID;
  name: string;
  type: "inference" | "training" | "computation";
  implementationScriptPath: string;
  setupScriptPath?: string;
  defaultArgs?: Record<string, unknown>;
  description: string;
  createdAt: string;
  updatedAt: string;
  inputObjectGroupDescriptions: FunctionInputObjectGroupDesc[];
  outputObjectGroupDescriptions: FunctionOutputObjectGroupDesc[];
  outputVariableDescriptions: FunctionOutputVariableDesc[];
}

