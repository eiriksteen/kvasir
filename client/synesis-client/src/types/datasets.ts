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
}

export interface Automation {
  id: string;
  name: string;
  description: string;
  datasetIds: string[];
} 