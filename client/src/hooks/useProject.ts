import { fetchProjects, createProject, updateProjectDetails, fetchProjectNodes, updateNodePosition, createNode, deleteNode, addEntityToProject, removeEntityFromProject } from "@/lib/api";
import { Project, ProjectCreate, ProjectDetailsUpdate } from "@/types/project";
import { FrontendNode, FrontendNodeCreate } from "@/types/node";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { useCallback, useMemo } from "react";
import { UUID } from "crypto";


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
  const selectedProject = useMemo(() => projects.find(project => project.id === projectId), [projects, projectId]);

  // Fetch nodes for the selected project
  const { data: frontendNodes, error: nodesError, isLoading: nodesLoading, mutate: mutateNodes } = useSWR(
    session && selectedProject ? ['projectNodes', selectedProject.id] : null,
    () => fetchProjectNodes(session?.APIToken?.accessToken || '', projectId),
    { fallbackData: [] }
  );

  // Update node position
  const { trigger: updatePosition } = useSWRMutation(
    session && selectedProject ? ['projectNodes', selectedProject.id] : null,
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
    session && selectedProject ? ['projectNodes', selectedProject.id] : null,
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
    session && selectedProject ? ['projectNodes', selectedProject.id] : null,
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
    if (!selectedProject) return;

    await triggerUpdateProject({data, projectId: selectedProject.id});
    
    mutateNodes();
  }, [selectedProject, triggerUpdateProject, mutateNodes]);

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
  const addEntity = async (entityType: "data_source" | "dataset" | "analysis" | "automation", entityId: string) => {
    if (!selectedProject) return;

    const position = calculateNodePosition();

    // Create the node for the entity
    await createFrontendNode({
      projectId: selectedProject.id,
      xPosition: position.x,
      yPosition: position.y,
      type: entityType,
      dataSourceId: entityType === "data_source" ? entityId : null,
      datasetId: entityType === "dataset" ? entityId : null,
      analysisId: entityType === "analysis" ? entityId : null,
      automationId: entityType === "automation" ? entityId : null,
    });

    // Update the project to include the entity
    await addEntityToProject(session?.APIToken?.accessToken || '', selectedProject.id, {
      entityType,
      entityId: entityId as UUID,
    });

    mutateProjects();
  };

  // Unified function to remove any entity from project
  const removeEntity = async (entityType: "data_source" | "dataset" | "analysis" | "automation", entityId: string) => {
    if (!selectedProject) return;

    // Update the project to remove the entity
    await removeEntityFromProject(session?.APIToken?.accessToken || '', selectedProject.id, {
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
      case "automation":
        nodeToDelete = frontendNodes?.find(node => node.automationId === entityId);
        break;
    }
    
    if (nodeToDelete) {
      await deleteNodeTrigger(nodeToDelete.id);
    }
  };

  return {
    projects,
    selectedProject,
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
