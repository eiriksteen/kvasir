import { useSession } from 'next-auth/react';
import { fetchProjectNodes, updateNodePosition, createNode } from '@/lib/api';
import useSWR from 'swr';
import useSWRMutation from 'swr/mutation';
import { FrontendNode, FrontendNodeCreate } from '@/types/node';

export function useNode(projectId: string) {
  console.log("projectId in useNode", projectId);
  const { data: session } = useSession();

  // Fetch nodes for the project
  const { data: frontendNodes, error, isLoading, mutate: mutateNodes } = useSWR(
    session && projectId ? 'projectNodes' : null,
    () => fetchProjectNodes(session?.APIToken?.accessToken || '', projectId),
    { fallbackData: [] }
  );
  console.log("frontendNodes in useNode", frontendNodes);

  // Update node position
  const { trigger: updatePosition } = useSWRMutation(
    'updateNodePosition',
    async (_, { arg }: { arg: FrontendNode }) => {
      const node = frontendNodes?.find(n => n.id === arg.id);
      if (!node) return frontendNodes;

      const updatedNode = await updateNodePosition(
        session?.APIToken?.accessToken || '',
        arg
      );

      return frontendNodes?.map(n => n.id === arg.id ? updatedNode : n) || [];
    },
    {
      populateCache: (newData) => newData,
      revalidate: false
    }
  );

  const { trigger: createFrontendNode } = useSWRMutation(
    'createNode',
    async (_, { arg }: { arg: FrontendNodeCreate }) => {
      return await createNode(session?.APIToken?.accessToken || '', arg);
    },
  );

  return {
    frontendNodes,
    error,
    isLoading,
    updatePosition,
    createFrontendNode
  };
}
