import { UUID } from "crypto";

export type Modality = "time_series" | "tabular";

// DB Schemas

export interface DatasetInDB {
  id: UUID;
  userId: UUID;
  name: string;
  description: string;
  additionalVariables?: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
}

export interface DataObjectInDB {
  id: UUID;
  name: string;
  groupId: UUID;
  originalId: string;
  description?: string | null;
  additionalVariables?: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
}

export interface ObjectGroupInDB {
  id: UUID;
  name: string;
  description: string;
  modality: Modality;
  datasetId: UUID;
  originalIdName?: string | null;
  additionalVariables?: Record<string, unknown> | null;
  rawDataReadScriptPath?: string | null;
  rawDataReadFunctionName?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface TimeSeriesInDB {
  id: UUID; // Foreign key to data_object.id
  startTimestamp: string;
  endTimestamp: string;
  numTimestamps: number;
  samplingFrequency: "m" | "h" | "d" | "w" | "y" | "irr";
  timezone: string;
  featuresSchema: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface TimeSeriesGroupInDB {
  id: UUID;
  totalTimestamps: number;
  numberOfSeries: number;
  // None if varying between series
  samplingFrequency?: "m" | "h" | "d" | "w" | "y" | "irr" | null;
  // None if varying between series
  timezone?: string | null;
  // None if varying between series
  featuresSchema?: Record<string, unknown> | null;
  earliestTimestamp: string;
  latestTimestamp: string;
  createdAt: string;
  updatedAt: string;
}

// Schemas for the API

export interface DataObject extends DataObjectInDB {
  modalityFields: TimeSeriesInDB; // TODO: Add more modalities when implemented
}

export interface ObjectGroup extends ObjectGroupInDB {
  modalityFields: TimeSeriesGroupInDB; // TODO: Add more modalities when implemented
}

export interface Dataset extends DatasetInDB {
  objectGroups: ObjectGroup[];
}

export interface ObjectGroupWithObjects extends ObjectGroup {
  objects: DataObject[];
}

export interface GetDatasetsByIDsRequest {
  datasetIds: UUID[];
}

// Create schemas

export interface TimeSeriesCreate {
  originalId: string;
  startTimestamp: string;
  endTimestamp: string;
  numTimestamps: number;
  samplingFrequency: "m" | "h" | "d" | "w" | "y" | "irr";
  timezone: string;
  featuresSchema: Record<string, unknown>;
}

export interface TimeSeriesGroupCreate {
  totalTimestamps: number;
  numberOfSeries: number;
  // None if varying between series
  samplingFrequency?: "m" | "h" | "d" | "w" | "y" | "irr" | null;
  // None if varying between series
  timezone?: string | null;
  // None if varying between series
  featuresSchema?: Record<string, unknown> | null;
  earliestTimestamp: string;
  latestTimestamp: string;
}

export interface DataObjectCreate {
  originalId: string;
  description?: string | null;
  modalityFields: TimeSeriesCreate; // TODO: Add more modalities when implemented
}

export interface ObjectsFile {
  filename: string;
  modality: Modality;
}

export interface DataObjectGroupCreate {
  name: string;
  originalIdName: string;
  description: string;
  modality: string;
  modalityFields: TimeSeriesGroupCreate; // TODO: Add more modalities when implemented
  objectsFiles: ObjectsFile[]; // Objects that belong to this group
}

export interface DatasetCreate {
  name: string;
  description: string;
  // TODO: Add more modalities
  groups: DataObjectGroupCreate[];
}

// Raw data schemas

export interface TimeSeriesRawDataParams {
  startTimestamp: string;
  endTimestamp: string;
}

export interface TimeSeriesRawData {
  data: Record<string, Array<[string, number | string]>>; // Dict[str, List[Tuple[datetime, Union[float, int]]]]
  params: TimeSeriesRawDataParams;
}

export interface DataObjectRawData{
  originalId: string;
  modality: Modality;
  data: TimeSeriesRawData; // TODO: Add more modalities when implemented
}

export interface GetRawDataRequest {
  projectId: UUID;
  objectId: UUID;
  args: TimeSeriesRawDataParams;
}