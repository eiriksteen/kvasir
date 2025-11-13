import { WaitlistCreate, WaitlistInDB } from "@/types/waitlist";
import useSWRMutation from "swr/mutation";
import { camelToSnakeKeys, snakeToCamelKeys } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function joinWaitlist(waitlistData: WaitlistCreate): Promise<WaitlistInDB> {
  const response = await fetch(`${API_URL}/waitlist/join`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(waitlistData))
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to join waitlist' }));
    throw new Error(errorData.detail || `Failed to join waitlist: ${response.status}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export const useWaitlist = () => {
  const { trigger: triggerJoinWaitlist, isMutating, error } = useSWRMutation(
    "waitlist",
    async (_, { arg }: { arg: WaitlistCreate }) => {
      return await joinWaitlist(arg);
    }
  );

  return { 
    joinWaitlist: triggerJoinWaitlist, 
    isJoining: isMutating, 
    error 
  };
};

