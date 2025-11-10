import { useSession } from "next-auth/react";
import useSWRMutation from "swr/mutation";
import { UUID } from "crypto";
import { camelToSnakeKeys } from "@/lib/utils";

const PROJECT_SERVER_URL = process.env.NEXT_PUBLIC_PROJECT_API_URL;

export interface RunExtractionRequest {
  projectId: UUID;
  promptContent: string;
  runId?: UUID | null;
}

async function runExtractionEndpoint(
  token: string,
  extractionRequest: RunExtractionRequest
): Promise<void> {
  const response = await fetch(`${PROJECT_SERVER_URL}/agents/run-extraction`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(camelToSnakeKeys(extractionRequest)),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to run extraction", errorText);
    throw new Error(`Failed to run extraction: ${response.status} ${errorText}`);
  }
}

export const useExtraction = () => {
  const { data: session } = useSession();

  const { trigger: runExtraction, isMutating: isRunningExtraction } = useSWRMutation(
    session ? "run-extraction" : null,
    async (_, { arg }: { arg: RunExtractionRequest }) => {
      await runExtractionEndpoint(
        session ? session.APIToken.accessToken : "",
        arg
      );
    }
  );

  return {
    runExtraction,
    isRunningExtraction,
  };
};

