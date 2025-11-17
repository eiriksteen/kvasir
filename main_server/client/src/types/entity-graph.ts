import { UUID } from "crypto";

export type EntityType = "data_source" | "dataset" | "analysis" | "pipeline" | "model_instantiated";

// =============================================================================
// Edge and Graph Types
// =============================================================================

export interface EdgePoints {
  dataSources: UUID[];
  datasets: UUID[];
  analyses: UUID[];
  pipelines: UUID[];
  modelsInstantiated: UUID[];
  pipelineRuns: UUID[];
}

export interface GraphNode {
  id: UUID;
  name: string;
  description: string;
  fromEntities: EdgePoints;
  toEntities: EdgePoints;
}

export interface PipelineGraphNode extends GraphNode {
  runs: GraphNode[];
}

export interface EntityGraph {
  dataSources: GraphNode[];
  datasets: GraphNode[];
  pipelines: PipelineGraphNode[];
  analyses: GraphNode[];
  modelsInstantiated: GraphNode[];
}

// =============================================================================
// Edge Points Using Names (for display/debugging)
// =============================================================================

export interface EdgePointsUsingNames {
  dataSources: string[];
  datasets: string[];
  analyses: string[];
  pipelines: string[];
  modelsInstantiated: string[];
  pipelineRuns: string[];
}

export interface GraphNodeUsingNames {
  id: UUID;
  name: string;
  description: string;
  fromEntities: EdgePointsUsingNames;
  toEntities: EdgePointsUsingNames;
}

export interface PipelineGraphNodeUsingNames extends GraphNodeUsingNames {
  runs: GraphNodeUsingNames[];
}

export interface EntityGraphUsingNames {
  dataSources: GraphNodeUsingNames[];
  datasets: GraphNodeUsingNames[];
  pipelines: PipelineGraphNodeUsingNames[];
  analyses: GraphNodeUsingNames[];
  modelsInstantiated: GraphNodeUsingNames[];
}

// =============================================================================
// Entity Details
// =============================================================================

export interface EntityDetail {
  entityId: UUID;
  entityType: EntityType;
  name: string;
  description: string;
  fromEntities: EdgePoints;
  toEntities: EdgePoints;
}

export interface EntityDetailsResponse {
  entityDetails: EntityDetail[];
}

// =============================================================================
// Create Models
// =============================================================================

export interface EntityEdge {
  fromEntityType: EntityType;
  fromEntityId: UUID;
  toEntityType: EntityType;
  toEntityId: UUID;
  fromPipelineRunId?: UUID | null;
  toPipelineRunId?: UUID | null;
}

export interface EntityEdgesCreate {
  edges: EntityEdge[];
}

