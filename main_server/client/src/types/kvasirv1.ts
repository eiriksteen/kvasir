import { UUID } from "crypto";

export type RunType = "swe" | "analysis" | "extraction" | "kvasir";
export type ResultType = "swe" | "analysis";
export type RunStatus = "pending" | "running" | "completed" | "failed" | "rejected" | "waiting";
export type MessageRole = "swe" | "analysis" | "kvasir" | "user";
export type MessageType = "tool_call" | "result" | "error" | "info" | "chat";


export interface RunBase {
  id: UUID;
  runName: string;
  userId: UUID;
  type: RunType;
  status: RunStatus;
  description?: string | null;
  projectId?: UUID | null;
  startedAt: string;
  completedAt?: string | null;
}

export interface Message {
  id: UUID;
  content: string;
  runId: UUID;
  role: MessageRole;
  type: MessageType;
  createdAt: string;
}

export interface PydanticAIMessage {
  id: UUID;
  runId: UUID;
  messageList: Uint8Array;
  createdAt: string;
}

export interface ResultsQueue {
  id: UUID;
  runId: UUID;
  content: string[];
  createdAt: string;
}

export interface DepsBase {
  id: UUID;
  runId: UUID;
  type: RunType;
  content: string;
  createdAt: string;
}

export interface ResultBase {
  id: UUID;
  runId: UUID;
  type: ResultType;
  content: string;
  createdAt: string;
}

export interface AnalysisRun extends RunBase {
  analysisId: UUID;
  kvasirRunId: UUID;
  result: ResultBase;
}

export interface SweRun extends RunBase {
  kvasirRunId: UUID;
  result: ResultBase;
}

export interface RunCreate {
  id?: UUID | null;
  type: RunType;
  initialStatus?: RunStatus;
  runName?: string | null;
  projectId?: UUID | null;
}

export interface MessageCreate {
  content: string;
  runId: UUID;
  role: MessageRole;
  type: MessageType;
}

export interface ResultsQueueCreate {
  runId: UUID;
  content: string[];
}

export interface DepsCreate {
  runId: UUID;
  type: RunType;
  content: string;
}

export interface ResultCreate {
  runId: UUID;
  type: ResultType;
  content: string;
}

