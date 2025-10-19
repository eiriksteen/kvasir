import { UUID } from "crypto";

// DB Models

export interface RunSpecificationInDB {
  id: UUID;
  runName: string;
  planAndDeliverableDescriptionForUser: string;
  planAndDeliverableDescriptionForAgent: string;
  questionsForUser?: string | null;
  configurationDefaultsDescription?: string | null;
  createdAt: string;
  updatedAt: string;
}

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
}

export interface Run extends RunInDB {
  spec?: RunSpecificationInDB | null;
  inputs?: RunEntityIds | null;
  outputs?: RunEntityIds | null;
}
