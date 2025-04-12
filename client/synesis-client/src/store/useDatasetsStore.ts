import { TimeSeriesDataset } from "@/types/datasets";
import { create } from "zustand";

interface DatasetsStore {
  datasetsInContext: TimeSeriesDataset[];
  setDatasetsInContext: (datasets: TimeSeriesDataset[]) => void;
}

export const useDatasetsStore = create<DatasetsStore>((set) => ({
  datasetsInContext: [],
  setDatasetsInContext: (datasets) => set(() => ({ datasetsInContext: datasets })),
})); 