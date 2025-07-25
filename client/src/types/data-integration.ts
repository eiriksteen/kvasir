export type SupportedSource = "TabularFile" | "AWS S3" | "Azure Blob" | "GCP Storage" | "PostgreSQL" | "MongoDB";
import { Feature } from "@/types/data-objects";

export interface DataSourceBase {
  id: string;
  user_id: string;
  type: SupportedSource;
  name: string;
  description: string | null;
  qualityDescription: string | null;
  contentPreview: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface FileDataSource extends DataSourceBase {
  id: string;
  fileName: string;
  filePath: string;
  fileType: string;
  fileSizeBytes: number;
  createdAt: string;
  updatedAt: string;
};

export interface TabularFileDataSource extends FileDataSource {
  numRows: number;
  numColumns: number;
  features: Feature[];
}


export type DataSource = TabularFileDataSource // | Other data source types


export type IntegrationJobResult = {
  jobId: string;
  datasetId: string;
  codeExplanation: string;
  pythonCodePath: string;
};

