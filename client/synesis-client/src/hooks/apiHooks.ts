import { fetchDatasets, fetchJobs, fetchJob } from "@/lib/api";
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


export const useRefreshDatasets = (jobState: string) => {
  const {mutate} = useSWRConfig();
  
  useEffect(() => {
    if (jobState === "completed") {
      mutate(`${URL}/ontology/datasets`);
    }
  }, [jobState]);
};


export const useRefreshJobs = (jobState: string) => {
  const {mutate} = useSWRConfig();

  useEffect(() => {
    if (jobState !== "") {
      mutate(`${URL}/jobs`);
    }
  }, [jobState]);
};

export const useMonitorJobs = (
  jobState: string,
  setJobState: (jobState: string) => void,
  token: string
) => {

  const { data, error } = useSWR(
    jobState === "running" ? [`${URL}/jobs`, "monitor"] : null,
    () => fetchJobs(token, true),
    {
      refreshInterval: 2000
    }
  );

  console.log("DATA", data);
  console.log("JOB STATE", jobState);
  console.log("ERROR", error);

  useEffect(() => {
    console.log("RUNNING USE EFFECT");
    console.log("DATA", data);
    console.log("JOB STATE", jobState);
    console.log("ERROR", error);
    if (data) {
      console.log("RUNNING IF");
      if (data.some(job => job.status === "failed")) {
        console.log("RUNNING IF 1");
        setJobState("failed");
      }
      else if (data?.length === 0) {
        console.log("RUNNING ELSE IF");
        setJobState("completed");
      }
    }

  }, [data]);

  return {
    jobsInProgress: data,
    isError: error,
  };
};
