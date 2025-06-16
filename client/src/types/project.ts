export interface Project {
    id: string;
    userId: string;
    name: string;
    description: string;
    createdAt: string;
    updatedAt: string;
    datasetIds: string[];
    analysisIds: string[];
    automationIds: string[];
}

export interface ProjectCreate {
    name: string;
    description: string;
}

export interface ProjectUpdate {
    name?: string;
    description?: string;
    type?: "dataset" | "analysis" | "automation";
    id?: string;
    remove?: boolean;
}
