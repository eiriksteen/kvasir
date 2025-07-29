import { fetchProjects, createProject, updateProject, fetchProjectNodes, updateNodePosition, createNode, deleteNode } from "@/lib/api";
import { Project, ProjectCreate, ProjectUpdate } from "@/types/project";
import { FrontendNode, FrontendNodeCreate } from "@/types/node";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { useCallback, useMemo } from "react";


export const useProjects = () => {
  const { data: session } = useSession();

  const { data: projects, error, isLoading } = useSWR(
    session ? "projects" : null,
    () => fetchProjects(session ? session.APIToken.accessToken : ""),
    { fallbackData: [] }
  );

  const {trigger: triggerUpdateProject} = useSWRMutation(
    "projects",
    async (_, { arg }: { arg: { data: ProjectUpdate, projectId: string } }) => {
      const updatedProject = await updateProject(
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

  return { projects, error, isLoading, triggerUpdateProject, triggerCreateNewProject };
}

export const useProject = (projectId: string) => {
  const { data: session } = useSession();
  const { projects, triggerUpdateProject } = useProjects();

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

  const updateProjectAndNode = useCallback(async (data: ProjectUpdate) => {
    if (!selectedProject) return;

    await triggerUpdateProject({data, projectId: selectedProject.id});
    
    mutateNodes();
  }, [selectedProject, triggerUpdateProject, mutateNodes]);

  const calculateDatasetPosition = useCallback(() => {
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

  const addDataSourceToProject = async (sourceId: string) => {
    if (!selectedProject) return;

    const position = calculateDatasetPosition();

    // First create the node for the dataset
    await createFrontendNode({
      projectId: selectedProject.id,
      xPosition: position.x,
      yPosition: position.y,
      type: "data_source",
      dataSourceId: sourceId,
      datasetId: null,
      analysisId: null,
      automationId: null,
    });

    // Then update the project to include the dataset
    await updateProjectAndNode({
      type: "data_source",
      id: sourceId,
      remove: false,
    });
  };

  // Remove dataset from project and delete corresponding node
  const removeDataSourceFromProject = async (sourceId: string) => {
    if (!selectedProject) return;

    // First update the project to remove the dataset
    await updateProjectAndNode({
      type: "data_source",
      id: sourceId,
      remove: true,
    });

    // Then find and delete the corresponding node
    const nodeToDelete = frontendNodes?.find(node => node.dataSourceId === sourceId);
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
    addDataSourceToProject,
    removeDataSourceFromProject,
    calculateDatasetPosition,
  };
};
