import { UUID } from "crypto";

// DB Models

export interface RunInDB {
  id: UUID;
  userId: UUID;
  type: string;
  status: string;
  startedAt: string;
  conversationId?: UUID | null;
  parentRunId?: UUID | null;
  completedAt?: string | null;
  runName?: string | null;
}

export interface RunMessageInDB {
  id: UUID;
  content: string;
  runId: UUID;
  type: "tool_call" | "result" | "error";
  createdAt: string;
}

export interface DataIntegrationRunInputInDB {
  runId: UUID;
  targetDatasetDescription: string;
  createdAt: string;
  updatedAt: string;
}

export interface ModelIntegrationRunInputInDB {
  runId: UUID;
  modelIdStr: string;
  source: "github" | "pip" | "source_code";
}

export interface DataIntegrationRunResultInDB {
  runId: UUID;
  datasetId: UUID;
  codeExplanation: string;
  pythonCodePath: string;
}

export interface ModelIntegrationRunResultInDB {
  runId: UUID;
  modelId: UUID;
}

// API Models

export interface DataIntegrationRunInput {
  runId: UUID;
  targetDatasetDescription: string;
  dataSourceIds: UUID[];
}

export type RunInput = DataIntegrationRunInput | ModelIntegrationRunInputInDB;
export type RunResult = DataIntegrationRunResultInDB | ModelIntegrationRunResultInDB;

export interface Run extends RunInDB {
  input?: RunInput | null;
  result?: RunResult | null;
}
