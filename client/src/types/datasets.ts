export interface TimeSeriesDataset {
  id: string;
  userId: string;
  name: string;
  description: string;
  numSeries: number;
  numFeatures: number;
  avgNumTimestamps: number;
  maxNumTimestamps: number;
  minNumTimestamps: number;
  indexFirstLevel: string;
  indexSecondLevel?: string;
  createdAt: string;
  updatedAt: string;
  type: "timeSeries";
}

export interface Datasets {
  timeSeries: TimeSeriesDataset[];
}

export interface TimeSeriesData {
  id: string;
  originalId: string;
  timestamps: Date[];
  values: number[][];
  featureNames: string[];
}

export interface EntityMetadata {
  datasetId: string;
  entityId: string;
  originalId: string;
  originalIdName: string;
  columnNames: string[];
  columnTypes: string[];
  values: string[] | number[] | boolean[] | null[];
}