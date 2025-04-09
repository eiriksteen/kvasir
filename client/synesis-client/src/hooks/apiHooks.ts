import { fetchDatasets, fetchJobs, streamChat, fetchMessages, createConversation, updateContext } from "@/lib/api";
import { Job } from "@/types/jobs";
import { ChatMessage } from "@/types/chat";
import { useEffect, useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { apiMessageToChatMessage } from "@/lib/utils";
import { useSession } from "next-auth/react";
import { Automation } from "@/types/automations";
import { TimeSeriesDataset } from "@/types/datasets";
const URL = process.env.NEXT_PUBLIC_API_URL;

// TODO: data fetching needs optimization
// in useRefreshDatasets and useRefreshJobs, only new data should be fetched

// TODO: simplify job monitoring logic
// on load, fetch all jobs
// among all jobs, put current running jobs in monitoring list
// upon job add through interface, add to monitoring list
// check status of of these continuously through web polling
// on job removed from /running-jobs, remove from monitoring list and check results through API call
// alternatively, create API endpoint that receives a list of job ids and returns their statuses
//      (on job status change, update monitoring list)

export const useDatasets = () => {
  const {data: session} = useSession();

  if (!session) {
    return {
      datasets: {
        timeSeries: [],
        numDatasets: 0,
      },
      isLoading: false,
      isError: false,
    };
  }

  const { data, error, isLoading } = useSWR(`${URL}/ontology/datasets`, () => fetchDatasets(session.APIToken.accessToken));

  return {
    datasets: data,
    isLoading,
    isError: error,
  };
};


export const useJobs = () => {
  const {data: session} = useSession();

  if (!session) {
    return {
      jobs: [],
      isLoading: false,
      isError: false,
    };
  }

  const { data, error, isLoading } = useSWR(`${URL}/jobs`, () => fetchJobs(session.APIToken.accessToken));

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
  addedJobs: Job[],
  setAddedJobs: (addedJobs: Job[]) => void) => {

  const {data: session} = useSession();

  if (!session) {
    return;
  }

  const { data, error } = useSWR(
    addedJobs.length > 0 ? [`${URL}/jobs`, addedJobs] : null,
    () => fetchJobs(session.APIToken.accessToken, true),
    {
      refreshInterval: 2000
    }
  );

  useEffect(() => {

    if (data) {
      if (data?.length === 0) {
        setAddedJobs([]);
      }
    }

  }, [data]);

  return {
    jobsInProgress: data,
    isError: error,
  };
};


export const useCreateConversation = (setConversationId: (conversationId: string) => void) => {

  const {data: session} = useSession();

  if (!session) {
    return;
  }

  useEffect(() => {
    createConversation(session.APIToken.accessToken).then((conversation) => {
      setConversationId(conversation.id);
    });
  }, []);
};


export const useChat = (prompt: string, token: string, conversationId: string | null ) => {
  const [response, setResponse] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([{"role": "user", "content": prompt}]);


  useEffect(() => {
    if (conversationId) {
      fetchMessages(token, conversationId).then((messages) => {
        setMessages(messages.map(apiMessageToChatMessage));
      });
    }
  }, []);


  useEffect(() => {
    (async () => {
      if (prompt === "" || !conversationId) {
        return;
      }
      let newMessages: ChatMessage[] = [{"role": "user", "content": prompt}];
      if (response !== "") {
        newMessages = [{role: "assistant", content: response}, {"role": "user", "content": prompt}];
      }
      setMessages([...messages, ...newMessages]);
      setResponse("");
      const stream = streamChat(token, prompt, conversationId);
      for await (const chunk of stream) {
        setResponse(chunk);
      }
    })();
  }, [prompt]);

  return { response, messages };
};

export const useUpdateContext = (conversationId: string | null, datasetsInContext: TimeSeriesDataset[], automationsInContext: Automation[]) => {
  const {data: session} = useSession();

  // if (!session || !conversationId) {
  //   return;
  // }

  useEffect(() => {
    if (!session || !conversationId) {
      return;
    }
    const datasetIds = datasetsInContext.map((dataset) => dataset.id);
    const automationIds = automationsInContext.map((automation) => automation.id);
    updateContext(session.APIToken.accessToken, conversationId, datasetIds, automationIds).then((data) => {
      console.log(data);
    });

  }, [datasetsInContext, automationsInContext]);
}