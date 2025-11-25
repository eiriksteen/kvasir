import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { UUID } from "crypto";
import { snakeToCamelKeys, camelToSnakeKeys } from "@/lib/utils";
import {
  EntityGraph,
  EntityNode,
  EntityNodeCreate,
  EdgeDefinition,
  NodeGroupBase,
  NodeGroupCreate,
} from "@/types/ontology/entity-graph";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Fetch entity graph
async function fetchEntityGraph(
  token: string,
  rootGroupId?: UUID | null,
  rootNodeId?: UUID | null
): Promise<EntityGraph> {
  const params = new URLSearchParams();
  if (rootGroupId) params.append("root_group_id", rootGroupId);
  if (rootNodeId) params.append("root_node_id", rootNodeId);

  const url = `${API_URL}/entity-graph/entity-graph${params.toString() ? `?${params.toString()}` : ""}`;

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

// Add node
async function addNode(token: string, node: EntityNodeCreate): Promise<EntityNode> {
  const response = await fetch(`${API_URL}/entity-graph/node`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(camelToSnakeKeys(node)),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to add node", errorText);
    throw new Error(`Failed to add node: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

// Get node
async function getNode(token: string, nodeId: UUID): Promise<EntityNode> {
  const response = await fetch(`${API_URL}/entity-graph/node/${nodeId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to get node", errorText);
    throw new Error(`Failed to get node: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

// Update node position
async function updateNodePosition(token: string, nodeId: UUID, xPosition: number, yPosition: number): Promise<EntityNode> {
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

// Get node edges
async function getNodeEdges(token: string, nodeId: UUID): Promise<EdgeDefinition[]> {
  const response = await fetch(`${API_URL}/entity-graph/node/${nodeId}/edges`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to get node edges", errorText);
    throw new Error(`Failed to get node edges: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

// Get node groups
async function getNodeGroups(
  token: string,
  nodeId?: UUID,
  groupIds?: UUID[]
): Promise<NodeGroupBase[]> {
  const params = new URLSearchParams();
  if (nodeId) params.append("node_id", nodeId);
  if (groupIds && groupIds.length > 0) {
    groupIds.forEach((id) => params.append("group_ids", id));
  }

  const url = `${API_URL}/entity-graph/node-groups${params.toString() ? `?${params.toString()}` : ""}`;

  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to get node groups", errorText);
    throw new Error(`Failed to get node groups: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

// Create node group
async function createNodeGroup(token: string, nodeGroup: NodeGroupCreate): Promise<NodeGroupBase> {
  const response = await fetch(`${API_URL}/entity-graph/node-group`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(camelToSnakeKeys(nodeGroup)),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to create node group", errorText);
    throw new Error(`Failed to create node group: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

// Delete node group
async function deleteNodeGroup(token: string, nodeGroupId: UUID): Promise<void> {
  const response = await fetch(`${API_URL}/entity-graph/node-group/${nodeGroupId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Failed to delete node group", errorText);
    throw new Error(`Failed to delete node group: ${response.status} ${errorText}`);
  }
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
export const useEntityGraph = (rootGroupId?: UUID | null, rootNodeId?: UUID | null) => {
  const { data: session } = useSession();

  const { data: entityGraph, mutate: mutateEntityGraph, error, isLoading } = useSWR(
    session && rootGroupId
      ? ["entity-graph", rootGroupId]
      : null,
    () =>
      fetchEntityGraph(
        session ? session.APIToken.accessToken : "",
        rootGroupId,
        rootNodeId
      )
  );

  // Add node mutation
  const { trigger: triggerAddNode } = useSWRMutation(
    session && rootGroupId
      ? ["entity-graph", rootGroupId]
      : null,
    async (_, { arg }: { arg: EntityNodeCreate }) => {
      await addNode(session ? session.APIToken.accessToken : "", arg);
      await mutateEntityGraph();
    }
  );

  // Delete node mutation
  const { trigger: triggerDeleteNode } = useSWRMutation(
    session && rootGroupId
      ? ["entity-graph", rootGroupId]
      : null,
    async (_, { arg }: { arg: { nodeId: UUID } }) => {
      await deleteNode(session ? session.APIToken.accessToken : "", arg.nodeId);
      await mutateEntityGraph();
    }
  );

  // Update node position mutation
  const { trigger: triggerUpdateNodePosition } = useSWRMutation(
    session && rootGroupId
      ? ["entity-graph", rootGroupId]
      : null,
    async (_, { arg }: { arg: { nodeId: UUID; xPosition: number; yPosition: number } }) => {
      await updateNodePosition(session ? session.APIToken.accessToken : "", arg.nodeId, arg.xPosition, arg.yPosition);
      await mutateEntityGraph();
    }
  );

  // Create edges mutation
  const { trigger: triggerCreateEdges } = useSWRMutation(
    session && rootGroupId
      ? ["entity-graph", rootGroupId]
      : null,
    async (_, { arg }: { arg: EdgeDefinition[] }) => {
      await createEdges(session ? session.APIToken.accessToken : "", arg);
      await mutateEntityGraph();
    }
  );

  // Remove edges mutation
  const { trigger: triggerRemoveEdges } = useSWRMutation(
    session && rootGroupId
      ? ["entity-graph", rootGroupId]
      : null,
    async (_, { arg }: { arg: EdgeDefinition[] }) => {
      await removeEdges(session ? session.APIToken.accessToken : "", arg);
      await mutateEntityGraph();
    }
  );

  // Add node to group mutation
  const { trigger: triggerAddNodeToGroup } = useSWRMutation(
    session && rootGroupId
      ? ["entity-graph", rootGroupId]
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
    session && rootGroupId
      ? ["entity-graph", rootGroupId]
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
    triggerAddNode,
    triggerDeleteNode,
    triggerUpdateNodePosition,
    triggerCreateEdges,
    triggerRemoveEdges,
    triggerAddNodeToGroup,
    triggerRemoveNodesFromGroups,
  };
};

// Hook for individual node operations
export const useEntityNode = (nodeId: UUID) => {
  const { data: session } = useSession();

  const { data: node, mutate: mutateNode, error, isLoading } = useSWR(
    session && nodeId ? ["entity-node", nodeId] : null,
    () => getNode(session ? session.APIToken.accessToken : "", nodeId)
  );

  const { data: nodeEdges, mutate: mutateNodeEdges } = useSWR(
    session && nodeId ? ["entity-node-edges", nodeId] : null,
    () => getNodeEdges(session ? session.APIToken.accessToken : "", nodeId)
  );

  return {
    node,
    nodeEdges,
    mutateNode,
    mutateNodeEdges,
    error,
    isLoading,
  };
};

// Hook for node groups
export const useNodeGroups = (nodeId?: UUID, groupIds?: UUID[]) => {
  const { data: session } = useSession();

  const { data: nodeGroups, mutate: mutateNodeGroups, error, isLoading } = useSWR(
    session ? ["node-groups", nodeId, groupIds] : null,
    () =>
      getNodeGroups(session ? session.APIToken.accessToken : "", nodeId, groupIds)
  );

  // Create node group mutation
  const { trigger: triggerCreateNodeGroup } = useSWRMutation(
    session ? ["node-groups", nodeId, groupIds] : null,
    async (_, { arg }: { arg: NodeGroupCreate }) => {
      const newGroup = await createNodeGroup(
        session ? session.APIToken.accessToken : "",
        arg
      );
      await mutateNodeGroups();
      return newGroup;
    }
  );

  // Delete node group mutation
  const { trigger: triggerDeleteNodeGroup } = useSWRMutation(
    session ? ["node-groups", nodeId, groupIds] : null,
    async (_, { arg }: { arg: { nodeGroupId: UUID } }) => {
      await deleteNodeGroup(
        session ? session.APIToken.accessToken : "",
        arg.nodeGroupId
      );
      await mutateNodeGroups();
    }
  );

  return {
    nodeGroups,
    mutateNodeGroups,
    error,
    isLoading,
    triggerCreateNodeGroup,
    triggerDeleteNodeGroup,
  };
};

