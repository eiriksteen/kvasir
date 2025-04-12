import { fetchJobs, fetchJobsBatch, postDataset } from "@/lib/api";
import { AnalysisJobInput, AutomationJobInput, IntegrationJobInput, Job, JobCategory } from "@/types/jobs";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";

interface JobStateResult {
  integrationState: string;
  analysisState: string;
  automationState: string;
  jobsAreRunning: boolean;
}

const computeJobState = (jobs: Job[]): JobStateResult => {
      const result: JobStateResult = {
      integrationState: "",
      analysisState: "",
      automationState: "",
      jobsAreRunning: false
    }

    if (!jobs) return result;

    const getJobState = (jobs: Job[]) => {
      if (jobs.some(job => job.status === "running")) return "running";
      if (jobs.some(job => job.status === "failed")) return "failed";
      if (jobs.some(job => job.status === "completed")) return "completed";
      return "";
    };

    const categories: JobCategory[] = ["integration", "analysis", "automation"];
    for (const category of categories) {
      const categoryJobs = jobs.filter((job) => job.type === category);
      result[`${category}State`] = getJobState(categoryJobs);
    }

  result.jobsAreRunning = result.integrationState === "running" || result.analysisState === "running" || result.automationState === "running";

  return result;
}

const emptyJobState: JobStateResult = {
  integrationState: "",
  analysisState: "",
  automationState: "",
  jobsAreRunning: false
}

export const useJobs = () => {
  const {data: session} = useSession();
  const {data: jobs, mutate: mutateJobs, isLoading, error} = useSWR(session ? "jobs" : null, () => fetchJobs(session ? session.APIToken.accessToken : "", false));
  const {data: jobState, mutate: mutateJobState} = useSWR(jobs ? "jobState" : null, {fallbackData: emptyJobState})
  const {trigger: triggerJob} = useSWRMutation(session ? "jobs" : null, async (_, {arg}: {arg: IntegrationJobInput | AnalysisJobInput | AutomationJobInput}) => {
    if (arg.type === "integration") {
      const newJob = await postDataset(session ? session.APIToken.accessToken : "", arg.file, arg.data_description);
      if (jobs) {
        return [newJob, ...jobs];
      }
      return [newJob];
    }
    // TODO: Implement analysis and automation job triggers
  }, {
    onSuccess: () => {
      mutateJobState({...jobState, jobsAreRunning: true, integrationState: "running"}, {revalidate: false});
    }
  });


  const {data: runningJobs} = useSWR(jobs && jobState.jobsAreRunning ? "jobsToMonitor" : null, async () => {
    if (!jobs) return [];
    const runningJobIds = jobs.filter(job => job.status === "running").map(job => job.id);
    if (runningJobIds.length === 0) return [];
    const jobsUpdated = await fetchJobsBatch(session ? session.APIToken.accessToken : "", runningJobIds);
    const jobsStopped = jobsUpdated.filter((job) => job.status !== "running");
    const jobsStillRunning = jobsUpdated.filter((job) => job.status === "running");

    console.log("STATE OF JOBS")
    console.log("jobsStopped", jobsStopped);
    console.log("jobsStillRunning", jobsStillRunning);
    console.log("jobs", jobs);

    // If there are no jobs still running, update the job state to reflect the result of the stopped jobs
    if (jobsStillRunning.length === 0) {
      const newJobState = computeJobState(jobsStopped);
      mutateJobState(newJobState, {revalidate: false});

      setTimeout(() => {
        mutateJobState(emptyJobState, {revalidate: false});
      }, 5000);
    }

    // If there are jobs that have stopped running, update the jobs list to reflect the new states
    if (jobsStopped.length > 0) {
      const updatedJobs = jobs.map(job => {
        const updatedJob = jobsStopped.find(stoppedJob => stoppedJob.id === job.id);
        return updatedJob || job;
      });
      mutateJobs(updatedJobs, {revalidate: false});
    }

    return jobsStillRunning;
  }, {
    refreshInterval: 2000
  });

  

  return { jobs, triggerJob, isLoading, error, jobState, runningJobs };
};