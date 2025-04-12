import { Job } from "@/types/jobs";
import { create } from "zustand";

interface JobStore {
    jobs: Job[];
    setJobs: (jobs: Job[]) => void;
}

export const useJobStore = create<JobStore>((set) => ({
    jobs: [],
    setJobs: (jobs: Job[]) => set({ jobs }),
}));


