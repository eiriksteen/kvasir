import { UUID } from "crypto";


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
    id: UUID;
    groupId: UUID;
    originalId: string;
    name: string;
    description: string;
    additionalVariables: Record<string, unknown>;
    createdAt: string;
    updatedAt: string;
}

export type ObjectGroup = {
    id: UUID;
    datasetId: UUID;
    name: string;
    description: string;
    originalIdName: string | null;
    savePath: string;
    structureType: string;
    createdAt: string;
    updatedAt: string;
    features: Feature[];
}

export type VariableGroup = {
    id: UUID;
    datasetId: UUID;
    name: string;
    description: string;
    savePath: string;
    createdAt: string;
    updatedAt: string;
}

export type Variable = {
    id: UUID;
    variableGroupId: UUID;
    name: string;
    pythonType: string;
    description: string;
}

export type VariableGroupWithVariables = VariableGroup & {
    variables: Variable[];
}

export interface TimeSeries extends DataObject {
    numTimestamps: number;
    startTimestamp: string;
    endTimestamp: string;
    samplingFrequency: "m" | "h" | "d" | "w" | "y" | "irr";
    timezone: string;
    type: "time_series";
}

export interface TimeSeriesWithRawData extends TimeSeries {
    data: Record<string, Array<[string, number | string]>>;
    features: Record<string, Feature>;
}

export interface TimeSeriesAggregation extends DataObject {
    isMultiSeriesComputation: boolean;
    type: "time_series_aggregation";
}

export interface ObjectGroupWithObjectList extends ObjectGroup {
    objects: (TimeSeries | TimeSeriesAggregation)[];
}

export type DatasetSources = {
    dataSourceIDs: UUID[];
    datasetIDs: UUID[];
    pipelineIDs: UUID[];
}

export type Dataset = {
    id: UUID;
    userId: UUID;
    name: string;
    description: string;
    modality: "time_series" | "image" | "text" | "audio" | "video";
    createdAt: string;
    updatedAt: string;
    objectGroups: ObjectGroup[];
    variableGroups: VariableGroupWithVariables[];
    sources: DatasetSources;
}

export type RawDataStructure = {
    data: Record<`${string},${string}`, Array<number | string | boolean | Date | null>>;
}

export interface AggregationObject {
    id: UUID;
    datasetId: UUID;
    name: string;
    description: string;
    createdAt: string;
    updatedAt: string;
    analysisResultId: UUID | null;
}

export type AggregationOutput = {
    outputData: RawDataStructure;
}

export type AggregationObjectWithRawData = AggregationObject & {
    data: AggregationOutput;
}


