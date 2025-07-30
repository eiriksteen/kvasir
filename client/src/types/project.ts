import { UUID } from "crypto";

export interface Project {
    id: string;
    userId: string;
    name: string;
    description: string;
    createdAt: string;
    updatedAt: string;
    dataSourceIds: string[];
    datasetIds: string[];
    analysisIds: string[];
    automationIds: string[];
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
    entityType: "data_source" | "dataset" | "analysis" | "automation";
    entityId: UUID;
}

export interface RemoveEntityFromProject {
    entityType: "data_source" | "dataset" | "analysis" | "automation";
    entityId: UUID;
}
