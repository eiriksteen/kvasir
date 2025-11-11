import { UUID } from "crypto";

export type DataSourceType = "file";
export type SupportedSource = "tabular_file" | "key_value_file";

// DB Models

export interface DataSourceInDB {
  id: UUID;
  userId: UUID;
  type: DataSourceType;
  name: string;
  additionalVariables?: Record<string, unknown> | null;
  createdAt: string;
}

export interface FileDataSourceInDB {
  id: UUID;
  fileName: string;
  filePath: string;
  fileType: string;
  fileSizeBytes: number;
  createdAt: string;
  updatedAt: string;
}

// API Models

export interface DataSource extends DataSourceInDB {
  // Add more possibilities here
  // Optional until agent has filled it (we want the data source to show up right away so we allow it to be null until then)
  typeFields?: FileDataSourceInDB | null;
}

export interface GetDataSourcesByIDsRequest {
  dataSourceIds: UUID[];
}

// Create models

export interface DataSourceCreate {
  name: string;
  type: DataSourceType;
  // In addition to general extra info, this can be used to store info about "wildcard" sources that we don't have dedicated tables for
  // We don't need to create fill the tables below
}

export interface FileDataSourceCreate {
  name: string;
  fileName: string;
  filePath: string;
  fileType: string;
  fileSizeBytes: number;
}

export interface TabularFileDataSourceCreate extends FileDataSourceCreate {
  // These are stored as additional variables on the file data source DB model
  // Don't want to create a new table for each file category
  jsonSchema: string;
  pandasDfInfo: string;
  pandasDfHead: string;
  numRows: number;
  numColumns: number;
  missingFractionPerColumn: string;
  iqrAnomaliesFractionPerColumn: string;
}
