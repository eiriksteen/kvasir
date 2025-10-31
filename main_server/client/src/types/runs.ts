import { UUID } from "crypto";

export type RunType = "swe" | "analysis" | "extraction";

// DB Models

export interface RunInDB {
  id: UUID;
  userId: UUID;
  type: RunType;
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

export interface RunPydanticMessageInDB {
  id: UUID;
  runId: UUID;
  messageList: Uint8Array; // bytes in Python
  createdAt: string;
}

export interface DataSourceInRunInDB {
  runId: UUID;
  dataSourceId: UUID;
  createdAt: string;
}

export interface DatasetInRunInDB {
  runId: UUID;
  datasetId: UUID;
  createdAt: string;
}

export interface ModelEntityInRunInDB {
  runId: UUID;
  modelEntityId: UUID;
  createdAt: string;
}

export interface PipelineInRunInDB {
  runId: UUID;
  pipelineId: UUID;
  createdAt: string;
}

export interface AnalysisInRunInDB {
  runId: UUID;
  analysisId: UUID;
  createdAt: string;
}

export interface AnalysisFromRunInDB {
  runId: UUID;
  analysisId: UUID;
  createdAt: string;
}

export interface PipelineFromRunInDB {
  runId: UUID;
  pipelineId: UUID;
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

export interface StreamedCode {
  code: string;
  filename: string;
  target: "redis" | "taskiq" | "both";
  output: string;
  error: string;
  createdAt: string;
}

// Create Models

export interface RunCreate {
  type: RunType;
  initialStatus: "pending" | "running" | "completed" | "failed";
  runName: string;
  planAndDeliverableDescriptionForUser: string;
  planAndDeliverableDescriptionForAgent: string;
  questionsForUser?: string | null;
  configurationDefaultsDescription?: string | null;
  targetEntityId?: UUID | null;
  projectId?: UUID | null;
  conversationId?: UUID | null;
  dataSourcesInRun: UUID[];
  datasetsInRun: UUID[];
  modelEntitiesInRun: UUID[];
  pipelinesInRun: UUID[];
  analysesInRun: UUID[];
}

export interface RunMessageCreate {
  type: "tool_call" | "result" | "error";
  content: string;
  runId: UUID;
}

export interface RunMessageCreatePydantic {
  content: Uint8Array; // bytes in Python
  runId: UUID;
}

// Update Models

export interface RunStatusUpdate {
  runId: UUID;
  status: "running" | "completed" | "failed" | "rejected";
  summary?: string | null;
}
