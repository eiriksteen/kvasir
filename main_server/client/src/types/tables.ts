import { UUID } from "crypto";


// API Schemas
export interface TableColumn {
  name: string;
  unit?: string | null;
  numberOfSignificantDigits?: number | null;
}

export interface TableConfig {
    title: string;
    subtitle: string;
    columns: TableColumn[];
    showRowNumbers: boolean;
    maxRows: number | null;
    sortBy: string | null;
    sortOrder: 'asc' | 'desc' | null;
  }

export interface BaseTable {
  id: UUID;
  analysisResultId: UUID;
  tableConfig: TableConfig;
}

// CRUD Schemas
export interface TableColumnCreate {
  name: string;
  unit?: string | null;
}

export interface TableCreate {
  analysisResultId: UUID;
  tableConfig: TableConfig;
}

export interface TableUpdate {
  id: UUID;
  tableConfig: TableConfig;
}