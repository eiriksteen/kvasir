import { Run } from "./runs";


export type Feature = {
    name: string;
    unit: string;
    description: string;
    type: "numerical" | "categorical";
    subtype: "continuous" | "discrete";
    scale: "ratio" | "interval" | "ordinal" | "nominal";
    source: "data" | "metadata";
    categoryId: string | null;
}

export interface DataObject {
    id: string;
    groupId: string;
    originalId: string;
    name: string;
    description: string;
    additionalVariables: Record<string, unknown>;
    createdAt: string;
    updatedAt: string;
}

export type ObjectGroup = {
    id: string;
    name: string;
    description: string;
    originalIdName: string | null;
    role: "primary" | "annotated" | "derived";
    structureType: string;
    createdAt: string;
    updatedAt: string;
    features: Feature[];
}

export interface TimeSeries extends DataObject {
    numTimestamps: number;
    startTimestamp: string;
    endTimestamp: string;
    samplingFrequency: "m" | "h" | "d" | "w" | "y" | "irr";
    timezone: string;
}

export interface TimeSeriesAggregation extends DataObject {
    isMultiSeriesComputation: boolean;
}

export interface ObjectGroupWithObjectList extends ObjectGroup {
    objects: (TimeSeries | TimeSeriesAggregation)[];
}

export type Dataset = {
    id: string;
    userId: string;
    name: string;
    description: string;
    modality: "time_series" | "image" | "text" | "audio" | "video";
    createdAt: string;
    updatedAt: string;
    primaryObjectGroup: ObjectGroup;
    annotatedObjectGroups: ObjectGroup[];
    computedObjectGroups: ObjectGroup[];
    integrationJobs: Run[];
}

export type DatasetWithObjectLists = {
    id: string;
    userId: string;
    name: string;
    description: string;
    modality: "time_series" | "image" | "text" | "audio" | "video";
    createdAt: string;
    updatedAt: string;
    primaryObjectGroup: ObjectGroupWithObjectList;
    annotatedObjectGroups: ObjectGroupWithObjectList[];
    computedObjectGroups: ObjectGroupWithObjectList[];
    integrationJobs: Run[];
}
