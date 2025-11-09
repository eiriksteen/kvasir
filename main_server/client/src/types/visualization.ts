import { UUID } from "crypto";

// DB schemas

export interface ImageInDB {
  id: UUID;
  imagePath: string;
  createdAt: string;
}

export interface EchartInDB {
  id: UUID;
  chartScriptPath: string;
  createdAt: string;
}

export interface TableInDB {
  id: UUID;
  tablePath: string;
  createdAt: string;
}

// ResultTable for table data
export interface ResultTable {
  data: Record<string, unknown[]>;
  indexColumn: string;
}

