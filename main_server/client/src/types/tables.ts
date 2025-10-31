import { UUID } from "crypto";

// API Schemas

export interface TableColumn {
  name: string;
  unit?: string | null;
  numberOfSignificantDigits?: number | null;
}

export interface TableConfig {
  title: string;
  subtitle?: string | null;
  columns: TableColumn[];
  showRowNumbers: boolean;
  maxRows?: number | null;
  sortBy?: string | null;
  sortOrder?: string | null;
}

export interface BaseTable {
  id: UUID;
  analysisResultId: UUID;
  tableConfig: TableConfig;
}

// CRUD Schemas

export interface TableCreate {
  analysisResultId: UUID;
  tableConfig: TableConfig;
}

export interface TableUpdate {
  id: UUID;
  tableConfig: TableConfig;
}