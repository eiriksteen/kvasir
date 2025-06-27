import { fetchJobs, postIntegrationJob, createJobEventSource, postModelIntegrationJob } from "@/lib/api";
import { AnalysisJobInput, AutomationJobInput, IntegrationJobInput, Job, ModelIntegrationJobInput } from "@/types/jobs";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { SWRSubscriptionOptions } from "swr/subscription";
import useSWRSubscription from "swr/subscription";


type JobType = "integration" | "analysis" | "automation" | "model_integration";
type jobState = "running" | "failed" | "completed" | "paused" | "awaiting_approval" | "";


const computeJobState = (jobs: {id: string, status: string}[]): jobState => {
  if (!jobs) return "";
  if (jobs.some(job => job.status === "running")) return "running";
    if (jobs.some(job => job.status === "paused")) return "paused";
  if (jobs.some(job => job.status === "awaiting_approval")) return "awaiting_approval";
  if (jobs.some(job => job.status === "failed")) return "failed";
  if (jobs.some(job => job.status === "completed")) return "completed";
  return "";
}

const emptyJobState: jobState = ""


export const useJobs = (jobType: JobType) => {
  const { data: session } = useSession()

  const { data: jobState, mutate: mutateJobState } = useSWR(["JobState", jobType], {fallbackData: emptyJobState})

  const { data: jobs, mutate: mutateJobs } = useSWR(
    session ? ["jobs", jobType] : null, 
    () => fetchJobs(session ? session.APIToken.accessToken : "", false, jobType), 
    {fallbackData: [],
      onSuccess: (jobs: Job[]) => {
        const newJobState = computeJobState(jobs);
        if (newJobState === "running" || newJobState === "paused" || newJobState === "awaiting_approval") {
          mutateJobState(newJobState, {revalidate: false});
        }
      }
    }
  )

  useSWRSubscription(
    session && jobState === "running" ? ["jobStream", jobType, jobs] : null,
    (_, {next}: SWRSubscriptionOptions<Job[]>) => {
      const eventSource = createJobEventSource(session ? session.APIToken.accessToken : "", jobType);

      eventSource.onmessage = (event) => {
        const streamedJobs = JSON.parse(event.data);
        next(null, () => {

          const jobsStopped = streamedJobs.filter((job: Job) => job.status !== "running");
          const jobsStillRunning = streamedJobs.filter((job: Job) => job.status === "running");
          const updatedJobs = jobs.map((job: Job) => jobsStopped.find((stoppedJob: Job) => stoppedJob.id === job.id) || job);

          if (jobsStillRunning.length === 0) {
            const newJobState = computeJobState(jobsStopped);
            mutateJobState(newJobState, {revalidate: false});
            if (newJobState == "completed" || newJobState == "failed") {
              setTimeout(() => {
                mutateJobState(emptyJobState, {revalidate: false});
              }, 5000);
            }
          }

          mutateJobs(updatedJobs, {revalidate: false});

          // Return undefined since this is purely to update the jobs by listening to updates from the event source
          return undefined;
        });
      }
      eventSource.onerror = (event) => {
        console.error("Job event source error", event);
      }

      return () => eventSource.close();
    }
  )

  const {trigger: triggerJob} = useSWRMutation(
    session ? ["jobs", jobType] : null, 
    async (_: string[], {arg}: {arg: IntegrationJobInput | AnalysisJobInput | AutomationJobInput | ModelIntegrationJobInput}) => {
    // TODO: Implement analysis and automation job triggers
    if (arg.type === "integration") {
      const newJob = await postIntegrationJob(
        session ? session.APIToken.accessToken : "", 
        arg.files, 
        arg.data_description,
        arg.data_source
      );
      if (jobs) {
        return [...jobs, newJob];
      }
      return [newJob];
    }
    if (arg.type === "model_integration") {
      const newJob = await postModelIntegrationJob(
        session ? session.APIToken.accessToken : "", 
        arg.model_id, 
        arg.source
      );
      if (jobs) {
        return [...jobs, newJob];
      }
      return [newJob];
    }
  }, {
    onSuccess: () => {
      mutateJobState("running", {revalidate: false});
    }
  });

  const {trigger: updateJobs} = useSWRMutation(
    session ? ["jobs", jobType] : null,
    (_: string[], {arg}: {arg: {id: string, status: string}[]}) => {
      // update all jobs with the IDs in arg to the jobs in arg
      const updatedJobs = jobs.map((job: Job) => {
        const updatedJob = arg.find((updatedJob: {id: string, status: string}) => updatedJob.id === job.id);
        if (updatedJob) {
          return {...job, status: updatedJob.status};
        }
        return job;
      });
      const newJobState = computeJobState(arg);
      mutateJobState(newJobState, {revalidate: false});
      if (newJobState !== "running" && newJobState !== "paused" && newJobState !== "awaiting_approval") {
        setTimeout(() => {
          mutateJobState(emptyJobState, {revalidate: false});
        }, 5000);
      }
      return updatedJobs;
    }
  );

  return { jobs, triggerJob, updateJobs, jobState };
};
