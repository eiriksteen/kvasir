import { UUID } from "crypto";

// DB Schemas needed by API types

export interface FeatureInDB {
  name: string;
  description: string;
  type: "numerical" | "categorical";
  subtype: "continuous" | "discrete";
  scale: "ratio" | "interval" | "ordinal" | "nominal";
  createdAt: string;
  updatedAt: string;
  unit?: string | null;
}

export interface ObjectGroupInDB {
  id: UUID;
  datasetId: UUID;
  name: string;
  description: string;
  structureType: string;
  savePath: string;
  createdAt: string;
  updatedAt: string;
  originalIdName?: string | null;
}

export interface TimeSeriesObjectGroupInDB {
  id: UUID;
  timeSeriesDfSchema: string;
  timeSeriesDfHead: string;
  entityMetadataDfSchema: string;
  entityMetadataDfHead: string;
  featureInformationDfSchema: string;
  featureInformationDfHead: string;
  createdAt: string;
  updatedAt: string;
}

export interface TimeSeriesAggregationObjectGroupInDB {
  id: UUID;
  timeSeriesAggregationOutputsDfSchema: string;
  timeSeriesAggregationOutputsDfHead: string;
  timeSeriesAggregationInputsDfSchema: string;
  timeSeriesAggregationInputsDfHead: string;
  entityMetadataDfSchema: string;
  entityMetadataDfHead: string;
  featureInformationDfSchema: string;
  featureInformationDfHead: string;
  createdAt: string;
  updatedAt: string;
}

export interface VariableGroupInDB {
  id: UUID;
  datasetId: UUID;
  name: string;
  description: string;
  savePath: string;
  createdAt: string;
  updatedAt: string;
}

export interface TimeSeriesInDB {
  id: UUID;
  numTimestamps: number;
  startTimestamp: string;
  endTimestamp: string;
  samplingFrequency: "m" | "h" | "d" | "w" | "y" | "irr";
  timezone: string;
}

export interface TimeSeriesAggregationInDB {
  id: UUID;
  isMultiSeriesComputation: boolean;
}

export interface DataObjectInDB {
  id: UUID;
  name: string;
  structureType: string;
  groupId?: UUID | null;
  originalId?: string | null;
  description?: string | null;
  additionalVariables?: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
}

// API Schemas

export interface FeatureWithSource extends FeatureInDB {
  source: "data" | "metadata";
}

export interface ObjectGroup extends ObjectGroupInDB {
  structureFields: TimeSeriesObjectGroupInDB | TimeSeriesAggregationObjectGroupInDB;
  features: FeatureWithSource[];
}

export interface DataObject extends DataObjectInDB {
  structureFields: TimeSeriesInDB | TimeSeriesAggregationInDB;
}

export interface DatasetSources {
  dataSourceIds: UUID[];
  datasetIds: UUID[];
  pipelineIds: UUID[];
}

export interface Dataset {
  id: UUID;
  userId: UUID;
  name: string;
  description: string;
  createdAt: string;
  updatedAt: string;
  objectGroups: ObjectGroup[];
  variableGroups: VariableGroupInDB[];
  sources: DatasetSources;
}

export interface Column {
  name: string;
  valueType: string;
  values: Array<number | string | boolean | Date | null>;
}

export type RawDataStructure = {
    data: Column[];
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


export interface ObjectGroupWithObjects extends ObjectGroup {
  objects: DataObject[];
}
