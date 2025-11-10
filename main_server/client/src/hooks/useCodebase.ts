import { UUID } from "crypto";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import { snakeToCamelKeys } from "@/lib/utils";
import { ProjectPath } from "@/types/code";

const PROJECT_SERVER_URL = process.env.NEXT_PUBLIC_PROJECT_API_URL;

// Fetcher function for getting the codebase tree
async function fetchCodebaseTree(projectId: UUID, token: string): Promise<ProjectPath> {
  const response = await fetch(
    `${PROJECT_SERVER_URL}/code/codebase-tree?project_id=${projectId}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch codebase tree: ${response.statusText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data) as ProjectPath;
}

// Fetcher function for getting a specific file
async function fetchCodebaseFile(
  projectId: UUID,
  filePath: string,
  token: string
): Promise<string> {
  const response = await fetch(
    `${PROJECT_SERVER_URL}/code/codebase-file?project_id=${projectId}&file_path=${encodeURIComponent(filePath)}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch file: ${response.statusText}`);
  }

  return response.text();
}

// Hook for getting the codebase tree
export const useCodebaseTree = (projectId: UUID | null) => {
  const { data: session } = useSession();

  const { data: codebaseTree, error, mutate } = useSWR<ProjectPath | null>(
    session && projectId ? ["codebaseTree", projectId] : null,
    () => fetchCodebaseTree(projectId!, session!.APIToken.accessToken),
  );

  return {
    codebaseTree,
    error,
    mutate,
    isLoading: !codebaseTree && !error,
  };
};

// Hook for getting a specific file from the codebase
export const useCodebaseFile = (projectId: UUID | null, filePath: string | null) => {
  const { data: session } = useSession();

  const { data: fileContent, error, mutate } = useSWR<string | null>(
    session && projectId && filePath ? ["codebaseFile", projectId, filePath] : null,
    () => fetchCodebaseFile(projectId!, filePath!, session!.APIToken.accessToken),
  );

  return {
    fileContent,
    error,
    mutate,
    isLoading: !fileContent && !error && filePath !== null,
  };
};