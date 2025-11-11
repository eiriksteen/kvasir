import { UUID } from "crypto";

// DB Models

export interface ConversationInDB {
  id: UUID;
  userId: UUID;
  name: string;
  projectId: UUID;
  createdAt: string;
}

export interface RunInConversationInDB {
  conversationId: UUID;
  runId: UUID;
  contextId?: UUID | null;
  createdAt: string;
}

export interface ChatMessageInDB {
  id: UUID;
  content: string;
  conversationId: UUID;
  role: "user" | "assistant";
  type: "tool_call" | "chat";
  contextId?: UUID | null;
  createdAt: string;
}

export interface ChatPydanticMessageInDB {
  id: UUID;
  conversationId: UUID;
  messageList: Uint8Array; // bytes in Python
  createdAt: string;
}

export interface ContextInDB {
  id: UUID;
}

export interface DataSourceContextInDB {
  contextId: UUID;
  dataSourceId: UUID;
}

export interface DatasetContextInDB {
  contextId: UUID;
  datasetId: UUID;
}

export interface ModelEntityContextInDB {
  contextId: UUID;
  modelEntityId: UUID;
}

export interface PipelineContextInDB {
  contextId: UUID;
  pipelineId: UUID;
}

export interface AnalysisContextInDB {
  contextId: UUID;
  analysisId: UUID;
}

// API Models

export interface Context {
  id: UUID;
  dataSourceIds: UUID[];
  datasetIds: UUID[];
  pipelineIds: UUID[];
  analysisIds: UUID[];
  modelEntityIds: UUID[];
}

export interface ChatMessage extends ChatMessageInDB {
  context?: Context | null;
}

export interface Conversation {
  id: UUID;
  userId: UUID;
  name: string;
  projectId: UUID;
  createdAt: string;
}

export interface ImplementationApprovalResponse {
  approved: boolean;
  feedback?: string | null;
}

// Create Models

export interface ContextCreate {
  dataSourceIds: UUID[];
  datasetIds: UUID[];
  pipelineIds: UUID[];
  analysisIds: UUID[];
  modelEntityIds: UUID[];
}

export interface UserChatMessageCreate {
  content: string;
  conversationId: UUID;
  context?: ContextCreate | null;
  saveToDb: boolean;
}

export interface ConversationCreate {
  projectId: UUID;
}

export type Prompt = UserChatMessageCreate;