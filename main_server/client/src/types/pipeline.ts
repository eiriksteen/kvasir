import { UUID } from "crypto";
import { FunctionWithoutEmbedding } from "./function";
import { ObjectGroup } from "./data-objects";
import { RunInDB } from "./runs";

// Minimal DB Models needed by API types

export interface ModelEntityInPipelineInDB {
  modelEntityId: UUID;
  pipelineId: UUID;
  codeVariableName: string;
  createdAt: string;
  updatedAt: string;
}

export interface PipelinePeriodicScheduleInDB {
  id: UUID;
  pipelineId: UUID;
  startTime: string;
  endTime: string;
  scheduleDescription: string;
  cronExpression: string;
  createdAt: string;
  updatedAt: string;
}

export interface PipelineOnEventScheduleInDB {
  id: UUID;
  pipelineId: UUID;
  eventListenerScriptPath: string;
  eventDescription: string;
  createdAt: string;
  updatedAt: string;
}

export interface PipelineOutputObjectGroupDefinitionInDB {
  id: UUID;
  pipelineId: UUID;
  name: string;
  structureId: string;
  description: string;
  outputEntityIdName: string;
  createdAt: string;
  updatedAt: string;
}

// API Models

export interface PipelineSources {
  datasetIds: UUID[];
  modelEntityIds: UUID[];
}

export interface PipelineGraphNode {
  id: UUID;
  entityId: UUID;
  type: "dataset" | "function" | "model_entity";
  modelFunctionType?: "training" | "inference" | null;
  fromModelEntityIds: UUID[];
  fromFunctionIds: UUID[];
  fromDatasetIds: UUID[];
}

export interface PipelineGraph {
  nodes: PipelineGraphNode[];
}

export interface PipelineFull {
  id: UUID;
  userId: UUID;
  name: string;
  pythonFunctionName: string;
  filename: string;
  modulePath: string;
  description: string;
  docstring: string;
  args: Record<string, unknown>;
  argsSchema: Record<string, unknown>;
  outputVariablesSchema: Record<string, unknown>;
  implementationScriptPath: string;
  argsDataclassName: string;
  inputDataclassName: string;
  outputDataclassName: string;
  outputVariablesDataclassName: string;
  createdAt: string;
  updatedAt: string;
  functions: FunctionWithoutEmbedding[];
  modelEntities: ModelEntityInPipelineInDB[];
  runs: RunInDB[];
  periodicSchedules: PipelinePeriodicScheduleInDB[];
  onEventSchedules: PipelineOnEventScheduleInDB[];
  computationalGraph: PipelineGraph;
  sources: PipelineSources;
  inputObjectGroups: ObjectGroup[];
  outputObjectGroupDefinitions: PipelineOutputObjectGroupDefinitionInDB[];
}

// Type alias for usage in components
export type Pipeline = PipelineFull;
