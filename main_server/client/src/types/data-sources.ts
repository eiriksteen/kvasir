import { UUID } from "crypto";
import { FeatureInDB } from "@/types/data-objects";

export type SupportedSource = "tabular_file" | "key_value_file";

// DB Models

export interface DataSourceInDB {
  id: UUID;
  userId: UUID;
  type: SupportedSource;
  name: string;
  createdAt: string;
}

export interface TabularFileDataSourceInDB {
  id: UUID;
  fileName: string;
  filePath: string;
  fileType: string;
  fileSizeBytes: number;
  numRows: number;
  numColumns: number;
  jsonSchema: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
  contentPreview: string;
}

export interface KeyValueFileDataSourceInDB {
  id: UUID;
  fileName: string;
  filePath: string;
  fileType: string;
  fileSizeBytes: number;
  createdAt: string;
  updatedAt: string;
}

export interface DataSourceAnalysisInDB {
  id: UUID;
  dataSourceId: UUID;
  contentDescription: string;
  qualityDescription: string;
  edaSummary: string;
  cautions: string;
  createdAt: string;
  updatedAt: string;
}

// API Models

export interface TabularFileDataSource extends TabularFileDataSourceInDB {
  features: FeatureInDB[];
}

export interface DataSource extends DataSourceInDB {
  // type_fields is optional - only added after analysis completes
  typeFields?: TabularFileDataSourceInDB | KeyValueFileDataSourceInDB | null;
  // analysis is optional - only added after analysis completes  
  analysis?: DataSourceAnalysisInDB | null;
  descriptionForAgent: string;
}
