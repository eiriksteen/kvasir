import { UUID } from "crypto";

export interface ProjectDataSourceInDB {
    projectId: UUID;
    dataSourceId: UUID;
    xPosition: number;
    yPosition: number;
    createdAt: string;
    updatedAt: string;
}

export interface ProjectDatasetInDB {
    projectId: UUID;
    datasetId: UUID;
    xPosition: number;
    yPosition: number;
    createdAt: string;
    updatedAt: string;
}

export interface ProjectAnalysisInDB {
    projectId: UUID;
    analysisId: UUID;
    xPosition: number;
    yPosition: number;
    createdAt: string;
    updatedAt: string;
}

export interface ProjectPipelineInDB {
    projectId: UUID;
    pipelineId: UUID;
    xPosition: number;
    yPosition: number;
    createdAt: string;
    updatedAt: string;
}

export interface ProjectModelEntityInDB {
    projectId: UUID;
    modelEntityId: UUID;
    xPosition: number;
    yPosition: number;
    createdAt: string;
    updatedAt: string;
}

export interface ProjectDatasetBeingCreatedInDB {
    projectId: UUID;
    runId: UUID;
    xPosition: number;
    yPosition: number;
    createdAt: string;
    updatedAt: string;
}

export interface ProjectPipelineBeingCreatedInDB {
    projectId: UUID;
    runId: UUID;
    xPosition: number;
    yPosition: number;
    createdAt: string;
    updatedAt: string;
}

export interface ProjectModelEntityBeingCreatedInDB {
    projectId: UUID;
    runId: UUID;
    xPosition: number;
    yPosition: number;
    createdAt: string;
    updatedAt: string;
}

export interface Project {
    id: UUID;
    userId: UUID;
    name: string;
    description: string;
    dataSources: ProjectDataSourceInDB[];
    datasets: ProjectDatasetInDB[];
    analyses: ProjectAnalysisInDB[];
    pipelines: ProjectPipelineInDB[];
    modelEntities: ProjectModelEntityInDB[];
    datasetsBeingCreated: ProjectDatasetBeingCreatedInDB[];
    pipelinesBeingCreated: ProjectPipelineBeingCreatedInDB[];
    modelEntitiesBeingCreated: ProjectModelEntityBeingCreatedInDB[];
    createdAt: string;
    updatedAt: string;
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
    fromRunId?: UUID;
}

export interface RemoveEntityFromProject {
    projectId: UUID;
    entityType: "data_source" | "dataset" | "analysis" | "pipeline" | "model_entity";
    entityId: UUID;
}

export interface UpdateEntityPosition {
    projectId: UUID;
    entityType: "data_source" | "dataset" | "analysis" | "pipeline" | "model_entity";
    entityId: UUID;
    xPosition: number;
    yPosition: number;
}
