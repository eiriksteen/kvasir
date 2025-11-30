import { useSession } from "next-auth/react";
import useSWR from "swr";
import { UUID } from "crypto";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchImage(
  token: string,
  imageId: UUID,
  mountNodeId: UUID
): Promise<string> {
  const response = await fetch(
    `${API_URL}/visualization/images/${imageId}/download?mount_node_id=${mountNodeId}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to fetch image: ${response.status} ${errorText}`);
  }

  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);
  return blobUrl;
}

export const useImage = (imageId: UUID, mountNodeId: UUID) => {
  const { data: session } = useSession();

  const { data: imageBlobUrl, error, isLoading } = useSWR(
    session && imageId && mountNodeId ? ["image", imageId, mountNodeId] : null,
    () => fetchImage(session!.APIToken.accessToken, imageId, mountNodeId)
  );

  return {
    imageBlobUrl,
    isLoading,
    isError: error,
  };
};
