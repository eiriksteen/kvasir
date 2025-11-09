import { useSession } from "next-auth/react";
import useSWR from "swr";
import { UUID } from "crypto";

const PROJECT_API_URL = process.env.NEXT_PUBLIC_PROJECT_API_URL;

async function fetchImage(
  token: string,
  imageId: UUID
): Promise<string> {
  const response = await fetch(
    `${PROJECT_API_URL}/image/get-image/${imageId}`,
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

export const useImage = (imageId: UUID) => {
  const { data: session } = useSession();

  const { data: imageBlobUrl, error, isLoading } = useSWR(
    session && imageId ? ["image", imageId] : null,
    () => fetchImage(session ? session.APIToken.accessToken : "", imageId)
  );

  return {
    imageBlobUrl,
    isLoading,
    isError: error,
  };
};

