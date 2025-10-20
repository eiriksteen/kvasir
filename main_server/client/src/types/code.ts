import { UUID } from "crypto";

export type ScriptType = "function" | "model" | "pipeline" | "data_integration" | "analysis";

export interface ScriptInDB {
  id: UUID;
  userId: UUID;
  filename: string;
  path: string;
  modulePath: string;
  type: ScriptType;
  output: string | null;
  error: string | null;
  createdAt: string;
  updatedAt: string;
}

