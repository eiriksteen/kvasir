import { useSession } from "next-auth/react";
import useSWR from "swr";
import { UUID } from "crypto";
import { snakeToCamelKeys } from "@/lib/utils";
import { CodebasePath, CodebaseFile } from "@/types/ontology/code";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Fetch codebase tree
async function fetchCodebaseTree(
  token: string,
  mountGroupId: UUID
): Promise<CodebasePath> {
  const response = await fetch(`${API_URL}/codebase/${mountGroupId}/tree`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to fetch codebase tree", errorText);
    throw new Error(`Failed to fetch codebase tree: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data) as CodebasePath;
}

// Fetch codebase file
async function fetchCodebaseFile(
  token: string,
  mountGroupId: UUID,
  filePath: string
): Promise<CodebaseFile> {
  const params = new URLSearchParams({ file_path: filePath });
  const response = await fetch(
    `${API_URL}/codebase/${mountGroupId}/file?${params.toString()}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to fetch codebase file", errorText);
    throw new Error(`Failed to fetch codebase file: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data) as CodebaseFile;
}

// Hook for getting the codebase tree
export const useCodebaseTree = (mountGroupId: UUID | null) => {
  const { data: session } = useSession();
  
  const { data, mutate, error, isLoading } = useSWR(
    session && mountGroupId ? ["codebase-tree", mountGroupId] : null,
    () => fetchCodebaseTree(session!.APIToken.accessToken, mountGroupId!)
  );

  return {
    codebaseTree: data,
    error,
    mutate,
    isLoading,
  };
};

// Hook for getting a specific file from the codebase
export const useCodebaseFile = (
  mountGroupId: UUID | null,
  filePath: string | null
) => {
  const { data: session } = useSession();
  
  const { data, mutate, error, isLoading } = useSWR(
    session && mountGroupId && filePath
      ? ["codebase-file", mountGroupId, filePath]
      : null,
    () =>
      fetchCodebaseFile(
        session!.APIToken.accessToken,
        mountGroupId!,
        filePath!
      )
  );

  return {
    fileContent: data?.content ?? null,
    error,
    mutate,
    isLoading,
  };
};
