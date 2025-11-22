import useSWR from "swr";
import { RunBase, Message, MessageCreate, RunCreate } from "@/types/kvasirv1";
import { useCallback, useMemo } from "react";
import { useSession } from "next-auth/react";
import { UUID } from "crypto";
import { SSE } from 'sse.js';
import { snakeToCamelKeys, camelToSnakeKeys } from "@/lib/utils";
import { v4 as uuidv4 } from 'uuid';
import { useAgentContext } from "@/hooks/useAgentContext";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchRunMessages(token: string, runId: UUID): Promise<Message[]> {
  const response = await fetch(`${API_URL}/kvasir-v1/messages/${runId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch run messages', errorText);
    throw new Error(`Failed to fetch run messages: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function createRun(token: string, runCreate: RunCreate): Promise<RunBase> {
  const response = await fetch(`${API_URL}/kvasir-v1/run`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(runCreate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to create run', errorText);
    throw new Error(`Failed to create run: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

function createKvasirV1EventSource(token: string, message: MessageCreate): SSE {
  return new SSE(`${API_URL}/kvasir-v1/completions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    payload: JSON.stringify(camelToSnakeKeys(message))
  });
}

export const useRunMessages = (runId: UUID | null) => {
  const { data: session } = useSession();

  const { data: runMessages, mutate: mutateRunMessages, error, isLoading } = useSWR<Message[]>(
   session && runId ? ["runMessages", runId] : null, 
   async () => {
    if (runId) {
      return await fetchRunMessages(session!.APIToken.accessToken, runId);
    }
    else {
      return []
    }
  }
  );

  return {
    runMessages: runMessages || [],
    error,
    isLoading,
    mutateRunMessages
  }
}

export const useKvasirV1 = (projectId: UUID) => {
  const { data: session } = useSession();

  const { data: agentRunId, mutate: setAgentRunId } = useSWR(
    session ? ["agent-run-id", projectId] : null, {fallbackData: null}
  );
  const { runMessages, error, isLoading, mutateRunMessages } = useRunMessages(agentRunId);

  const { dataSourcesInContext, datasetsInContext, pipelinesInContext, analysesInContext, modelsInstantiatedInContext } = useAgentContext(projectId);

  const run = useMemo(() => {
    return null; // Will need to fetch run by ID if needed
  }, []);

  const submitPrompt = useCallback(async (content: string) => {
    if (session) {
      if (content === "") {
        return;
      }

      const isNewRun = !agentRunId;
      let runId = agentRunId;

      if (isNewRun) {
        const newRun = await createRun(session.APIToken.accessToken, {
          type: "kvasir",
          projectId: projectId,
        });
        runId = newRun.id;
        await setAgentRunId(newRun.id, {revalidate: false});
      }

      const userMessage: Message = {
        id: uuidv4() as UUID,
        role: "user", 
        type: "chat",
        runId: runId!,
        content: content,
        createdAt: new Date().toISOString(),
      };

      const prompt: MessageCreate = {
        context: {
          dataSources: dataSourcesInContext,
          datasets: datasetsInContext,
          pipelines: pipelinesInContext,
          analyses: analysesInContext,
          models: modelsInstantiatedInContext,
        },
        content: content,
        runId: runId!,
        role: "user",
        type: "chat",
      };

      mutateRunMessages([...runMessages, userMessage], {revalidate: false});

      const eventSource = createKvasirV1EventSource(session.APIToken.accessToken, prompt);

      eventSource.onmessage = (ev) => {
          const data: Message = snakeToCamelKeys(JSON.parse(ev.data));

          if (data.content === "DONE") {
            // Optionally refetch runs if needed
          }
          else {
            mutateRunMessages((prev: Message[] | undefined) => {
              if (!prev) return prev;
              // If message with the same id already exists, update it, else add it
              const existingMessage = prev.find((msg) => msg.id === data.id);
              if (existingMessage) {
                return prev.map((msg) => msg.id === data.id ? data : msg)
              }
              else {
                return [...prev, data]
              }
            }, {revalidate: false});
        }
      };
    }
  }, [
    session, 
    agentRunId, 
    projectId,
    setAgentRunId,
    mutateRunMessages,
    runMessages,
    dataSourcesInContext,
    datasetsInContext,
    pipelinesInContext,
    analysesInContext,
    modelsInstantiatedInContext,
  ]);

  const continueRun = useCallback(async (runId: UUID) => {

      const prompt: MessageCreate = {
        content: "Continue the conversation. If a run was completed suggest the next step or conclude the conversation if done. No need for long text here, something like 'The X run succeeded, and we can continue with building Y ...' is enough.",
        runId: runId,
        role: "user",
        type: "chat",
        context: {
          dataSources: dataSourcesInContext,
          datasets: datasetsInContext,
          pipelines: pipelinesInContext,
          analyses: analysesInContext,
          models: modelsInstantiatedInContext,
        },
      };

      const eventSource = createKvasirV1EventSource(session ? session.APIToken.accessToken : "", prompt);

      eventSource.onmessage = (ev) => {
          const data: Message = snakeToCamelKeys(JSON.parse(ev.data));

          if (data.content !== "DONE") {
              mutateRunMessages((prev: Message[] | undefined) => {
                if (!prev) return prev;
                // If message with the same id already exists, update it, else add it
                const existingMessage = prev.find((msg) => msg.id === data.id);
                if (existingMessage) {
                  return prev.map((msg) => msg.id === data.id ? data : msg)
                }
                else {
                  return [...prev, data]
                }
                
            }, {revalidate: false});

        }
      };

  }, [session, mutateRunMessages, dataSourcesInContext, datasetsInContext, pipelinesInContext, analysesInContext, modelsInstantiatedInContext]);



  return { 
    run,
    runMessages, 
    submitPrompt,
    continueRun,
    projectRunId: agentRunId,
    isLoading,
    isError: error,
    setAgentRunId
  };
}; 
