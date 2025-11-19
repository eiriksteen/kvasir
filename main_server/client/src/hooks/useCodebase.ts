import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRInfinite from "swr/infinite";
import { UUID } from "crypto";
import { snakeToCamelKeys } from "@/lib/utils";
import { CodebasePath, CodebaseFile, CodebaseFilePaginated } from "@/types/ontology/code";

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

// Fetch paginated codebase file
async function fetchCodebaseFilePaginated(
  token: string,
  mountGroupId: UUID,
  filePath: string,
  offset: number,
  limit: number
): Promise<CodebaseFilePaginated> {
  const params = new URLSearchParams({
    file_path: filePath,
    offset: offset.toString(),
    limit: limit.toString(),
  });
  const response = await fetch(
    `${API_URL}/codebase/${mountGroupId}/file/paginated?${params.toString()}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to fetch paginated codebase file", errorText);
    throw new Error(`Failed to fetch paginated codebase file: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data) as CodebaseFilePaginated;
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

// Hook for getting a specific file from the codebase with pagination
export const useCodebaseFilePaginated = (
  mountGroupId: UUID | null,
  filePath: string | null,
  linesPerPage: number = 100,
  maxLines: number = 500 // hardcoded max lines
) => {
  const { data: session } = useSession();
  
  const getKey = (pageIndex: number, previousPageData: CodebaseFilePaginated | null) => {
    // If we have previous data and it indicates no more data, stop fetching
    if (previousPageData && !previousPageData.hasMore) return null;
    
    // Check if we've reached the max line cap
    const currentOffset = pageIndex * linesPerPage;
    if (currentOffset >= maxLines) return null;
    
    // If we don't have session or required params, don't fetch
    if (!session || !mountGroupId || !filePath) return null;
    
    // Return the key for this page
    return [
      "codebase-file-paginated",
      mountGroupId,
      filePath,
      pageIndex * linesPerPage, // offset
      linesPerPage, // limit
    ];
  };

  const { data, size, setSize, error, isLoading, isValidating, mutate } = useSWRInfinite(
    getKey,
    ([, mountGroupId, filePath, offset, limit]) =>
      fetchCodebaseFilePaginated(
        session!.APIToken.accessToken,
        mountGroupId as UUID,
        filePath as string,
        offset as number,
        limit as number
      ),
    {
      revalidateFirstPage: false,
      revalidateAll: false,
    }
  );

  // Combine all pages of content
  const combinedContent = data?.map((page) => page.content).join("") ?? "";
  
  // Get metadata from the first page or last page
  const firstPage = data?.[0];
  const lastPage = data?.[data.length - 1];
  const totalLines = firstPage?.totalLines ?? 0;
  const loadedLines = lastPage ? lastPage.offset + lastPage.limit : 0;
  
  // Check if we can load more (considering both file end and max cap)
  const hasMoreInFile = lastPage?.hasMore ?? false;
  const hasReachedCap = loadedLines >= maxLines;
  const hasMore = hasMoreInFile && !hasReachedCap;

  const loadMore = () => {
    if (hasMore && !isValidating) {
      setSize(size + 1);
    }
  };

  return {
    fileContent: combinedContent || null,
    totalLines,
    loadedLines,
    hasMore,
    hasReachedCap,
    maxLines,
    loadMore,
    isLoading,
    isLoadingMore: isValidating && size > 0,
    error,
    mutate,
    size,
  };
};
