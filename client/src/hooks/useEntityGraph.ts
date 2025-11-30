import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { UUID } from "crypto";
import { snakeToCamelKeys, camelToSnakeKeys } from "@/lib/utils";
import {
  EntityGraph,
  GraphNode,
  EdgeDefinition,
} from "@/types/ontology/entity-graph";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Fetch entity graph
async function fetchEntityGraph(
  token: string,
  rootNodeId: UUID
): Promise<EntityGraph> {
  const url = `${API_URL}/entity-graph/entity-graph/${rootNodeId.toString()}`;

  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to fetch entity graph", errorText);
    throw new Error(`Failed to fetch entity graph: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}


// Update node position
async function updateNodePosition(token: string, nodeId: UUID, xPosition: number, yPosition: number): Promise<GraphNode> {
  const params = new URLSearchParams();
  params.append("x_position", xPosition.toString());
  params.append("y_position", yPosition.toString());

  const response = await fetch(`${API_URL}/entity-graph/node/${nodeId}/position?${params.toString()}`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json"
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to update node position", errorText);
    throw new Error(`Failed to update node position: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}
// Delete node
async function deleteNode(token: string, nodeId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/entity-graph/node/${nodeId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to delete node", errorText);
    throw new Error(`Failed to delete node: ${response.status} ${errorText}`);
  }
}

async function getLeafNodeByEntityId(
  token: string,
  entityId: UUID
): Promise<GraphNode> {
  const url = `${API_URL}/entity-graph/leaf-node/entity/${entityId.toString()}`;

  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to fetch leaf node by entity ID", errorText);
    throw new Error(`Failed to fetch leaf node by entity ID: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

// Add node to group
async function addNodeToGroup(token: string, nodeId: UUID, nodeGroupId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/entity-graph/node/${nodeId}/group/${nodeGroupId}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to add node to group", errorText);
    throw new Error(`Failed to add node to group: ${response.status} ${errorText}`);
  }
}

// Remove nodes from groups
async function removeNodesFromGroups(
  token: string,
  nodeIds: UUID[],
  nodeGroupIds: UUID[]
): Promise<void> {
  const params = new URLSearchParams();
  nodeIds.forEach((id) => params.append("node_ids", id));
  nodeGroupIds.forEach((id) => params.append("node_group_ids", id));

  const response = await fetch(`${API_URL}/entity-graph/nodes/groups?${params.toString()}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to remove nodes from groups", errorText);
    throw new Error(`Failed to remove nodes from groups: ${response.status} ${errorText}`);
  }
}

// Create edges
async function createEdges(token: string, edges: EdgeDefinition[]): Promise<void> {
  const response = await fetch(`${API_URL}/entity-graph/edges`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(camelToSnakeKeys(edges)),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to create edges", errorText);
    throw new Error(`Failed to create edges: ${response.status} ${errorText}`);
  }
}

// Remove edges
async function removeEdges(token: string, edges: EdgeDefinition[]): Promise<void> {
  const response = await fetch(`${API_URL}/entity-graph/edges`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(camelToSnakeKeys(edges)),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to remove edges", errorText);
    throw new Error(`Failed to remove edges: ${response.status} ${errorText}`);
  }
}

// Hook for entity graph operations
export const useEntityGraph = (rootNodeId?: UUID | null) => {
  const { data: session } = useSession();

  const { data: entityGraph, mutate: mutateEntityGraph, error, isLoading } = useSWR(
    session && rootNodeId
      ? ["entity-graph", rootNodeId]
      : null,
    () =>
      fetchEntityGraph(
        session ? session.APIToken.accessToken : "",
        rootNodeId!
      )
  );

  // Delete node mutation
  const { trigger: triggerDeleteNode } = useSWRMutation(
    session && rootNodeId
      ? ["entity-graph", rootNodeId]
      : null,
    async (_, { arg }: { arg: { nodeId: UUID } }) => {
      await deleteNode(session ? session.APIToken.accessToken : "", arg.nodeId);
      await mutateEntityGraph();
    }
  );

  // Update node position mutation
  const { trigger: triggerUpdateNodePosition } = useSWRMutation(
    session && rootNodeId
      ? ["entity-graph", rootNodeId]
      : null,
    async (_, { arg }: { arg: { nodeId: UUID; xPosition: number; yPosition: number } }) => {
      await updateNodePosition(session ? session.APIToken.accessToken : "", arg.nodeId, arg.xPosition, arg.yPosition);
      await mutateEntityGraph();
    }
  );

  // Create edges mutation
  const { trigger: triggerCreateEdges } = useSWRMutation(
    session && rootNodeId
      ? ["entity-graph", rootNodeId]
      : null,
    async (_, { arg }: { arg: EdgeDefinition[] }) => {
      await createEdges(session ? session.APIToken.accessToken : "", arg);
      await mutateEntityGraph();
    }
  );

  // Remove edges mutation
  const { trigger: triggerRemoveEdges } = useSWRMutation(
    session && rootNodeId
      ? ["entity-graph", rootNodeId]
      : null,
    async (_, { arg }: { arg: EdgeDefinition[] }) => {
      await removeEdges(session ? session.APIToken.accessToken : "", arg);
      await mutateEntityGraph();
    }
  );

  // Add node to group mutation
  const { trigger: triggerAddNodeToGroup } = useSWRMutation(
    session && rootNodeId
      ? ["entity-graph", rootNodeId]
      : null,
    async (_, { arg }: { arg: { nodeId: UUID; nodeGroupId: UUID } }) => {
      await addNodeToGroup(
        session ? session.APIToken.accessToken : "",
        arg.nodeId,
        arg.nodeGroupId
      );
      await mutateEntityGraph();
    }
  );

  // Remove nodes from groups mutation
  const { trigger: triggerRemoveNodesFromGroups } = useSWRMutation(
    session && rootNodeId
      ? ["entity-graph", rootNodeId]
      : null,
    async (_, { arg }: { arg: { nodeIds: UUID[]; nodeGroupIds: UUID[] } }) => {
      await removeNodesFromGroups(
        session ? session.APIToken.accessToken : "",
        arg.nodeIds,
        arg.nodeGroupIds
      );
      await mutateEntityGraph();
    }
  );

  return {
    entityGraph,
    mutateEntityGraph,
    error,
    isLoading,
    triggerDeleteNode,
    triggerUpdateNodePosition,
    triggerCreateEdges,
    triggerRemoveEdges,
    triggerAddNodeToGroup,
    triggerRemoveNodesFromGroups,
  };
};

// Hook for individual node operations
export const useEntityNode = (entityId: UUID) => {
  const { data: session } = useSession();

  const { data: node, mutate: mutateNode, error, isLoading } = useSWR(
    session && entityId ? ["entity-node", entityId] : null,
    () => getLeafNodeByEntityId(session ? session.APIToken.accessToken : "", entityId)
  );

  return {
    node,
    mutateNode,
    error,
    isLoading,
  };
};


