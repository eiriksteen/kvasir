// import { Feature } from "@/types/data-objects";
import { UUID } from "crypto";

export type SupportedSource = "file" | "s3" | "azure" | "gcp" | "psql" | "mongodb";

export interface DataSourceBase {
  id: UUID;
  user_id: string;
  type: SupportedSource;
  name: string;
  createdAt: string;
  updatedAt: string;
}

export interface TabularFileDataSource extends DataSourceBase {
  fileName: string;
  filePath: string;
  fileType: string;
  fileSizeBytes: number;
  numRows: number;
  numColumns: number;
  analysis: DataSourceAnalysis;
};

export interface DataSourceAnalysis {
  id: UUID;
  dataSourceId: UUID;
  contentDescription: string;
  qualityDescription: string;
  edaSummary: string;
  cautions: string;
  createdAt: string;
  updatedAt: string;
}

export type DataSource = DataSourceBase | TabularFileDataSource; // | Other data source types
