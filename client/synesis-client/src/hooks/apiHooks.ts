import { fetchDatasets, fetchJobs, fetchJob } from "@/lib/api";
import { Job } from "@/types/jobs";
import { useEffect, useRef, useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import useSWRSubscription from "swr/subscription";


const URL = process.env.NEXT_PUBLIC_API_URL;


export const useDatasets = (token: string) => {
  const { data, error, isLoading } = useSWR(`${URL}/ontology/datasets`, () => fetchDatasets(token));

  return {
    datasets: data,
    isLoading,
    isError: error,
  };
};


export const useJobs = (token: string) => {
  const { data, error, isLoading } = useSWR(`${URL}/jobs`, () => fetchJobs(token));

  return {
    jobs: data,
    isLoading,
    isError: error,
  };
};


export const useRefreshDatasets = (runningJobs: Job[]) => {
  const {mutate} = useSWRConfig();
  
  useEffect(() => {
    if (runningJobs.length === 0) {
      mutate(`${URL}/ontology/datasets`);
    }
  }, [runningJobs]);
};


export const useRefreshJobs = (runningJobs: Job[]) => {
  const {mutate} = useSWRConfig();

  useEffect(() => {
      mutate(`${URL}/jobs`);
  }, [runningJobs]);
};

export const useMonitorRunningJobs = (
  runningJobs: Job[],
  setRunningJobs: (runningJobs: Job[]) => void,
  token: string
) => {

  const { data, error } = useSWR(
    runningJobs.length > 0 ? [`${URL}/jobs`, runningJobs] : null,
    () => fetchJobs(token, true),
    {
      refreshInterval: 2000
    }
  );

  useEffect(() => {

    if (data) {
      if (data?.length === 0) {
        setRunningJobs([]);
      }
    }

  }, [data]);

  return {
    jobsInProgress: data,
    isError: error,
  };
};
