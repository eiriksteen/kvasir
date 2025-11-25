import useSWR from "swr";
import { RunBase, Message, MessageCreate, RunCreate } from "@/types/kvasirv1";
import { useCallback, useMemo } from "react";
import { useSession } from "next-auth/react";
import { UUID } from "crypto";
import { snakeToCamelKeys, camelToSnakeKeys } from "@/lib/utils";
import { v4 as uuidv4 } from 'uuid';
import { useAgentContext } from "@/hooks/useAgentContext";
import { useRunMessages } from "@/hooks/useRuns";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

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

async function postCompletion(token: string, message: MessageCreate): Promise<Message> {
  const response = await fetch(`${API_URL}/kvasir-v1/completions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(message))
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to get completion', errorText);
    throw new Error(`Failed to get completion: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export const useKvasirV1 = (projectId: UUID) => {
  const { data: session } = useSession();
  const { data: agentRunId, mutate: setAgentRunId } = useSWR(session ? ["agent-run-id", projectId] : null, {fallbackData: null});
  const { runMessages, mutateRunMessages } = useRunMessages(agentRunId, projectId);
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

      await postCompletion(session.APIToken.accessToken, prompt);
      // mutateRunMessages([...runMessages, userMessage, assistantMessage], {revalidate: false});
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

  return { 
    run,
    runMessages, 
    submitPrompt,
    projectRunId: agentRunId,
    setAgentRunId
  };
}; 
