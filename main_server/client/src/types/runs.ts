import { UUID } from "crypto";

// DB Models

export interface RunInDB {
  id: UUID;
  userId: UUID;
  type: "swe" | "analysis";
  status: "pending" | "running" | "completed" | "failed" | "rejected";
  runName: string;
  projectId?: UUID | null;
  conversationId?: UUID | null;
  planAndDeliverableDescriptionForUser: string;
  planAndDeliverableDescriptionForAgent: string;
  questionsForUser?: string | null;
  configurationDefaultsDescription?: string | null;
  startedAt: string;
  completedAt?: string | null;
}

export interface RunMessageInDB {
  id: UUID;
  content: string;
  runId: UUID;
  type: "tool_call" | "result" | "error";
  createdAt: string;
}

export interface RunCodeMessageInDB {
  id: UUID;
  code: string;
  filename: string;
  output: string | null;
  error: string | null;
  createdAt: string;
}


// API Models

export interface RunEntityIds {
  dataSourceIds: UUID[];
  datasetIds: UUID[];
  modelEntityIds: UUID[];
  pipelineIds: UUID[];
  analysisIds: UUID[];
}

export interface Run extends RunInDB {
  inputs?: RunEntityIds | null;
  outputs?: RunEntityIds | null;
}
