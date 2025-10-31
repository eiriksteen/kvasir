import { UUID } from "crypto";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import { SWRSubscriptionOptions } from "swr/subscription";
import useSWRSubscription from "swr/subscription";
import { SSE } from "sse.js";
import { snakeToCamelKeys } from "@/lib/utils";
import { useRun } from "./useRuns";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

interface StreamedCode {
  filename: string;
  code: string;
  output: string | null;
  error: string | null;
}

interface ScriptWithRawCode {
  id: UUID;
  userId: UUID;
  filename: string;
  path: string;
  modulePath: string;
  type: string;
  output: string | null;
  error: string | null;
  createdAt: string;
  updatedAt: string;
  code: string;
}

function createCodeStreamEventSource(token: string, runId: UUID): SSE {
  return new SSE(`${API_URL}/runs/stream-code/${runId}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
}

export const useCodeStream = (runId: UUID) => {
  const { data: session } = useSession();
  const { run } = useRun(runId);
  const { data: codeMessage, mutate: mutateCodeMessage } = useSWR<StreamedCode | null>(
    session ? ["codeStream", runId] : null,
    { fallbackData: null }
  );

  useSWRSubscription(
    session && run ? ["codeStream", runId, run.status] : null,
    (_, { next }: SWRSubscriptionOptions<StreamedCode | null>) => {
      if (!run || !session) {
        return () => {};
      }

      if (run.status === "running") {
        const eventSource = createCodeStreamEventSource(
          session.APIToken.accessToken,
          runId
        );

        eventSource.onmessage = (ev) => {

          const streamedCodes: StreamedCode[] = snakeToCamelKeys(JSON.parse(ev.data));
          // Get the most recent code message (last in the array)
          const mostRecentCode = streamedCodes[streamedCodes.length - 1];
          
          next(null, () => {
            mutateCodeMessage(mostRecentCode, { revalidate: false });
            return undefined;
          });
        };

        eventSource.onerror = (ev) => {
          console.error("Code stream event source error", ev);
        };

        return () => eventSource.close();
      } else {
        return () => {};
      }
    }
  );

  return { codeMessage };
};

// Fetcher function for getting script by ID
async function fetchScript(scriptId: UUID, token: string): Promise<ScriptWithRawCode> {
  const response = await fetch(`${API_URL}/code/script/${scriptId}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch script: ${response.statusText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data) as ScriptWithRawCode;
}

// Hook for getting a script by ID
export const useCode = (scriptId: UUID | null) => {
  const { data: session } = useSession();
  
  const { data: script, error, mutate } = useSWR<ScriptWithRawCode | null>(
    session && scriptId ? ["script", scriptId] : null,
    () => fetchScript(scriptId!, session!.APIToken.accessToken),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    }
  );

  return {
    script,
    error,
    mutate,
    isLoading: !script && !error,
  };
};