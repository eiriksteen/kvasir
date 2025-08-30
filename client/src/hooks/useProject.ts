import { Project, ProjectCreate, ProjectDetailsUpdate, AddEntityToProject, RemoveEntityFromProject } from "@/types/project";
import { FrontendNode, FrontendNodeCreate } from "@/types/node";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { useCallback, useMemo } from "react";
import { UUID } from "crypto";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchProjects(token: string): Promise<Project[]> {
  const response = await fetch(`${API_URL}/project/get-user-projects`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch projects', errorText);
    throw new Error(`Failed to fetch projects: ${response.status} ${errorText}`);
  }

  return response.json();
}

async function createProject(token: string, projectData: ProjectCreate): Promise<Project> {
  const response = await fetch(`${API_URL}/project/create-project`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(projectData)
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to create project', errorText);
    throw new Error(`Failed to create project: ${response.status} ${errorText}`);
  }

  return response.json();
}

async function updateProjectDetails(token: string, projectId: string, projectData: ProjectDetailsUpdate): Promise<Project> {
  const response = await fetch(`${API_URL}/project/update-project/${projectId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(projectData)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to update project details: ${response.status} ${errorText}`);
  }

  return response.json();
}

async function addEntityToProject(token: string, projectId: string, entityData: AddEntityToProject): Promise<Project> {
  const response = await fetch(`${API_URL}/project/add-entity/${projectId}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(entityData)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to add entity to project: ${response.status} ${errorText}`);
  }

  return response.json();
}

async function removeEntityFromProject(token: string, projectId: string, entityData: RemoveEntityFromProject): Promise<Project> {
  const response = await fetch(`${API_URL}/project/remove-entity/${projectId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(entityData)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to remove entity from project: ${response.status} ${errorText}`);
  }

  return response.json();
}

async function fetchProjectNodes(token: string, projectId: string): Promise<FrontendNode[]> {
  const response = await fetch(`${API_URL}/node/project/${projectId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch time series data', errorText);
    throw new Error(`Failed to fetch time series data: ${response.status} ${errorText}`);
  }

  return response.json();
}

async function updateNodePosition(token: string, node: FrontendNode): Promise<FrontendNode> {
  const response = await fetch(`${API_URL}/node/update-node/${node.id}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(node)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to update node position: ${response.status} ${errorText}`);
  }

  return response.json();
}

async function createNode(token: string, node: FrontendNodeCreate): Promise<FrontendNode> {
  const response = await fetch(`${API_URL}/node/create-node`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(node)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to create node: ${response.status} ${errorText}`);
  }

  return response.json();
}

async function deleteNode(token: string, nodeId: string): Promise<string> {
  const response = await fetch(`${API_URL}/node/delete/${nodeId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to delete node: ${response.status} ${errorText}`);
  }
  return response.json();
}


export const useProjects = () => {
  const { data: session } = useSession();

  const { data: projects, mutate: mutateProjects, error, isLoading } = useSWR(
    session ? "projects" : null,
    () => fetchProjects(session ? session.APIToken.accessToken : ""),
    { fallbackData: [] }
  );

  const {trigger: triggerUpdateProject} = useSWRMutation(
    "projects",
    async (_, { arg }: { arg: { data: ProjectDetailsUpdate, projectId: string } }) => {
      const updatedProject = await updateProjectDetails(
        session ? session.APIToken.accessToken : "",
        arg.projectId,
        arg.data
      );
      
      // return list of projects with updated project
      return projects?.map((project) =>
        project.id === updatedProject.id ? updatedProject : project
      );
      
    },
    { 
      populateCache: (updatedProjects) => updatedProjects,
      revalidate: false 
    }
  )

  // Create new project
  const { trigger: triggerCreateNewProject } = useSWRMutation(
    "projects",
    async (_, { arg }: { arg: ProjectCreate }) => {
      const newProject = await createProject(
        session ? session.APIToken.accessToken : "",
        arg
      );
      return newProject;
    },
    {
      populateCache: (newData: Project) => {
        if (projects) {
          return [...projects, newData];
        }
        return [newData];
      },
      revalidate: false
    }
  );

  return { projects, mutateProjects, error, isLoading, triggerUpdateProject, triggerCreateNewProject };
}

export const useProject = (projectId: string) => {
  const { data: session } = useSession();
  const { projects, mutateProjects, triggerUpdateProject } = useProjects();

  // Store selected project
  const project = useMemo(() => projects.find(project => project.id === projectId), [projects, projectId]);

  // Fetch nodes for the selected project
  const { data: frontendNodes, error: nodesError, isLoading: nodesLoading, mutate: mutateNodes } = useSWR(
    // Could use selectedProject.id as the second part of the key, but doing it this way will update the nodes also when the projects change
    session && project ? ['projectNodes', project] : null,
    () => fetchProjectNodes(session?.APIToken?.accessToken || '', projectId),
    { fallbackData: [] }
  );

  // Update node position
  const { trigger: updatePosition } = useSWRMutation(
    session && project ? ['projectNodes', project.id] : null,
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

  // Create node
  const { trigger: createFrontendNode } = useSWRMutation(
    session && project ? ['projectNodes', project.id] : null,
    async (_, { arg }: { arg: FrontendNodeCreate }) => {
      const res = await createNode(session?.APIToken?.accessToken || '', arg);
      return res;
    },
    {
      populateCache: (newNode) => {
        return [...(frontendNodes || []), newNode];
      },
      revalidate: false
    }
  );

  // Delete node
  const { trigger: deleteNodeTrigger } = useSWRMutation(
    session && project ? ['projectNodes', project.id] : null,
    async (_, { arg }: { arg: string } ) => {
      return await deleteNode(session?.APIToken?.accessToken || '', arg);
    },
    {
      populateCache: ( newData: string ) => {
        if (frontendNodes) {
          return frontendNodes.filter((node) => node.id !== newData);
        }
        return [];
      },
      revalidate: false
    }
  );

  const updateProjectAndNode = useCallback(async (data: ProjectDetailsUpdate) => {
    if (!project) return;

    await triggerUpdateProject({data, projectId: project.id});
    
    mutateNodes();
  }, [project, triggerUpdateProject, mutateNodes]);

  const calculateNodePosition = useCallback(() => {
    if (!frontendNodes) {
      return { x: -300, y: 0 };
    }

    const datasetNodes = frontendNodes.filter(node => node.type === "data_source");

    if (datasetNodes.length === 0) {
      return { x: -300, y: 0 };
    }

    const baseX = -300;
    const verticalSpacing = 75; 

    const yPositions = datasetNodes.map(node => node.yPosition);
    const highestY = Math.max(...yPositions);

    return { x: baseX, y: highestY + verticalSpacing };
  }, [frontendNodes]);


  // Unified function to add any entity to project
  const addEntity = async (entityType: "data_source" | "dataset" | "analysis" | "pipeline", entityId: string) => {
    if (!project) return;

    //const position = calculateNodePosition();

    // Create the node for the entity
    await createFrontendNode({
      projectId: project.id,
      xPosition: null,
      yPosition: null,
      type: entityType,
      dataSourceId: entityType === "data_source" ? entityId : null,
      datasetId: entityType === "dataset" ? entityId : null,
      analysisId: entityType === "analysis" ? entityId : null,
      pipelineId: entityType === "pipeline" ? entityId : null,
    });

    // Update the project to include the entity
    await addEntityToProject(session?.APIToken?.accessToken || '', project.id, {
      entityType,
      entityId: entityId as UUID,
    });

    mutateProjects();
  };

  // Unified function to remove any entity from project
  const removeEntity = async (entityType: "data_source" | "dataset" | "analysis" | "pipeline", entityId: string) => {
    if (!project) return;

    // Update the project to remove the entity
    await removeEntityFromProject(session?.APIToken?.accessToken || '', project.id, {
      entityType,
      entityId: entityId as UUID,
    });

    // Find and delete the corresponding node
    let nodeToDelete;
    switch (entityType) {
      case "data_source":
        nodeToDelete = frontendNodes?.find(node => node.dataSourceId === entityId);
        break;
      case "dataset":
        nodeToDelete = frontendNodes?.find(node => node.datasetId === entityId);
        break;
      case "analysis":
        nodeToDelete = frontendNodes?.find(node => node.analysisId === entityId);
        break;
      case "pipeline":
        nodeToDelete = frontendNodes?.find(node => node.pipelineId === entityId);
        break;
    }
    
    if (nodeToDelete) {
      await deleteNodeTrigger(nodeToDelete.id);
    }
  };

  return {
    project,
    frontendNodes,
    error: nodesError,
    isLoading: nodesLoading,
    updateProjectAndNode,
    updatePosition,
    createFrontendNode,
    deleteNodeTrigger,
    addEntity,
    removeEntity,
    calculateDatasetPosition: calculateNodePosition,
  };
};
