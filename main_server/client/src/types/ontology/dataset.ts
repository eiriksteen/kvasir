import { UUID } from "crypto";

export type Modality = "time_series" | "tabular";

export type SamplingFrequency = "m" | "h" | "d" | "w" | "y" | "irr";

// Base Models

export interface DatasetBase {
  id: UUID;
  userId: UUID;
  name: string;
  description: string;
  additionalVariables?: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
}

export interface DataObjectBase {
  id: UUID;
  name: string;
  groupId: UUID;
  originalId: string;
  description?: string | null;
  additionalVariables?: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
}

export interface ObjectGroupBase {
  id: UUID;
  name: string;
  description: string;
  modality: Modality;
  datasetId: UUID;
  originalIdName?: string | null;
  additionalVariables?: Record<string, unknown> | null;
  echartId?: UUID | null;
  createdAt: string;
  updatedAt: string;
}

export interface TimeSeriesBase {
  id: UUID; // Foreign key to data_object.id
  startTimestamp: string;
  endTimestamp: string;
  numTimestamps: number;
  samplingFrequency: SamplingFrequency;
  timezone?: string | null;
  featuresSchema: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface TimeSeriesGroupBase {
  id: UUID;
  totalTimestamps: number;
  numberOfSeries: number;
  // None if varying between series
  samplingFrequency?: SamplingFrequency | null;
  // None if varying between series
  timezone?: string | null;
  // None if varying between series
  featuresSchema?: Record<string, unknown> | null;
  earliestTimestamp: string;
  latestTimestamp: string;
  createdAt: string;
  updatedAt: string;
}

export interface TabularRowBase {
  id: UUID;
  featuresSchema: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface TabularGroupBase {
  id: UUID;
  numberOfEntities: number;
  numberOfFeatures: number;
  featuresSchema: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

// Composite Models

export interface DataObject extends DataObjectBase {
  modalityFields: TimeSeriesBase | TabularRowBase;
}

export interface ObjectGroup extends ObjectGroupBase {
  modalityFields: TimeSeriesGroupBase | TabularGroupBase;
  firstDataObject: DataObject;
}

export interface Dataset extends DatasetBase {
  objectGroups: ObjectGroup[];
}

export interface ObjectGroupWithObjects extends ObjectGroup {
  objects: DataObject[];
}

// Create Models

export interface DatasetBaseCreate {
  name: string;
  description?: string | null;
}

export interface TimeSeriesCreate {
  /**
   * Metadata for one time series object. Each DataFrame row represents one series.
   * Compute all values from actual data - don't assume values.
   */
  startTimestamp: string;
  endTimestamp: string;
  numTimestamps: number;
  samplingFrequency: SamplingFrequency;
  featuresSchema: Record<string, unknown>;
  timezone?: string | null;
}

export interface TimeSeriesGroupCreate {
  /**
   * Aggregated metadata computed from all time series in the group.
   * Values are computed by aggregating across all series (e.g., earliestTimestamp = min of all startTimestamps).
   */
  totalTimestamps: number;
  numberOfSeries: number;
  // None if varying between series
  samplingFrequency?: SamplingFrequency | null;
  // None if varying between series
  timezone?: string | null;
  // None if varying between series
  featuresSchema?: Record<string, unknown> | null;
  earliestTimestamp: string;
  latestTimestamp: string;
}

export interface TabularRowCreate {
  featuresSchema: Record<string, unknown>;
}

export interface TabularGroupCreate {
  numberOfEntities: number;
  numberOfFeatures: number;
  featuresSchema: Record<string, unknown>;
}

export interface DataObjectCreate {
  /**
   * Metadata for one data object. Each DataFrame row represents one object with its specific metadata.
   * Compute all values from actual data - don't assume values.
   */
  name: string;
  originalId: string;
  description?: string | null;
  modalityFields: TimeSeriesCreate | TabularRowCreate;
  [key: string]: unknown; // Allow extra fields
}

export interface ObjectsFile {
  filename: string;
  modality: Modality;
}

export interface ObjectGroupCreate {
  /**
   * Group of related data objects sharing the same modality.
   * objectsFiles: Parquet files where each row represents one data object with its metadata.
   * modalityFields: Aggregated statistics computed from all objects in the group.
   */
  name: string;
  originalIdName: string;
  description: string;
  modality: string;
  modalityFields: TimeSeriesGroupCreate | TabularGroupCreate;
  objectsFiles?: ObjectsFile[];
  [key: string]: unknown; // Allow extra fields
}

export interface DatasetCreate {
  /**
   * Complete dataset with object groups. Each group has:
   * - Parquet files (objectsFiles) where each row = one data object with computed metadata
   * - Aggregated group-level statistics (modalityFields)
   * Compute all values from actual data - don't assume!
   */
  name: string;
  description: string;
  groups?: ObjectGroupCreate[];
  [key: string]: unknown; // Allow extra fields
}

