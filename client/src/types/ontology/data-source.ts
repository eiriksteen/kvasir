import { UUID } from "crypto";

export type DataSourceType = "file";

// Base Models

export interface DataSourceBase {
  id: UUID;
  userId: UUID;
  type: DataSourceType;
  name: string;
  description: string;
  additionalVariables?: Record<string, unknown> | null;
  createdAt: string;
}

export interface FileDataSourceBase {
  id: UUID;
  fileName: string;
  filePath: string;
  fileType: string;
  fileSizeBytes: number;
  createdAt: string;
  updatedAt: string;
}

// Composite Models

export interface DataSource extends DataSourceBase {
  // Add more possibilities here
  // Optional until agent has filled it (we want the data source to show up right away so we allow it to be null until then)
  typeFields?: FileDataSourceBase | null;
}

// Create Models

export interface UnknownFileCreate {
  /**
   * This is for file types not covered by the other file create schemas.
   * It is for any type we haven't added yet.
   * NB: The file path must be an absolute path!
   */
  name: string;
  fileName: string;
  filePath: string;
  fileType: string;
  fileSizeBytes: number;
  [key: string]: unknown; // Allow extra fields
}

export interface TabularFileCreate extends UnknownFileCreate {
  /**
   * This is for tabular files, including csv, parquet, excel, etc.
   */
  jsonSchema: string;
  pandasDfInfo: string;
  pandasDfHead: string;
  numRows: number;
  numColumns: number;
  missingFractionPerColumn: string;
  iqrAnomaliesFractionPerColumn: string;
}

export interface DataSourceCreate {
  /**
   * Create a data source.
   * The name should reflect the actual source, for example files should be the file name including the extension.
   */
  name: string;
  description: string;
  type: DataSourceType;
  typeFields?: UnknownFileCreate | TabularFileCreate | null;
  [key: string]: unknown; // Allow extra fields
}

export interface DataSourceDetailsCreate {
  dataSourceId: UUID;
  typeFields: UnknownFileCreate | TabularFileCreate;
  [key: string]: unknown; // Allow extra fields
}

