import { UUID } from "crypto";

// API Models - Only what's used in frontend

export interface FunctionWithoutEmbedding {
  id: UUID;
  definitionId: UUID;
  version: number;
  argsSchema: Record<string, unknown>;
  defaultArgs: Record<string, unknown>;
  outputVariablesSchema: Record<string, unknown>;
  newestUpdateDescription: string;
  filename: string;
  modulePath: string;
  pythonFunctionName: string;
  implementationScriptPath: string;
  docstring: string;
  description: string;
  setupScriptPath?: string | null;
  createdAt: string;
  updatedAt: string;
}

// Type alias for backward compatibility
export type Function = FunctionWithoutEmbedding;
