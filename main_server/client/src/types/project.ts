import { UUID } from "crypto";

export interface Project {
    id: UUID;
    userId: UUID;
    name: string;
    description: string;
    createdAt: string;
    updatedAt: string;
    dataSourceIds: UUID[];
    datasetIds: UUID[];
    analysisIds: UUID[];
    pipelineIds: UUID[];
    modelEntityIds: UUID[];
}

export interface ProjectCreate {
    name: string;
    description: string;
}

export interface ProjectDetailsUpdate {
    name?: string;
    description?: string;
}

export interface AddEntityToProject {
    projectId: UUID;
    entityType: "data_source" | "dataset" | "analysis" | "pipeline" | "model_entity";
    entityId: UUID;
}

export interface RemoveEntityFromProject {
    projectId: UUID;
    entityType: "data_source" | "dataset" | "analysis" | "pipeline" | "model_entity";
    entityId: UUID;
}
