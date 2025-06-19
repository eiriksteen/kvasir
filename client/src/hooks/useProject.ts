import { fetchProjects, createProject, updateProject, fetchProjectNodes, updateNodePosition, createNode, deleteNode } from "@/lib/api";
import { Project, ProjectCreate, ProjectUpdate } from "@/types/project";
import { FrontendNode, FrontendNodeCreate } from "@/types/node";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";

export const useProject = () => {
  const { data: session } = useSession();

  // Fetch all projects
  const { data: projects, error, isLoading, mutate: mutateProjects } = useSWR(
    session ? "projects" : null,
    () => fetchProjects(session ? session.APIToken.accessToken : ""),
    { fallbackData: [] }
  );

  // Store selected project
  const { data: selectedProject, mutate: mutateSelectedProject } = useSWR(
    "selectedProject",
    { fallbackData: null }
  );

  // Fetch nodes for the selected project
  const { data: frontendNodes, error: nodesError, isLoading: nodesLoading, mutate: mutateNodes } = useSWR(
    session && selectedProject ? ['projectNodes', selectedProject.id] : null,
    () => fetchProjectNodes(session?.APIToken?.accessToken || '', selectedProject.id),
    { fallbackData: [] }
  );

  // Create new project
  const { trigger: createNewProject } = useSWRMutation(
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

  // Update project
  const { trigger: updateSelectedProject } = useSWRMutation(
    "projects",
    async (_, { arg }: { arg: { data: ProjectUpdate } }) => {
      const updatedProject = await updateProject(
        session ? session.APIToken.accessToken : "",
        selectedProject?.id || "",
        arg.data
      );
      
      return updatedProject;
    },
    {
      populateCache: (newData: Project) => {
        if (projects) {
          return projects.map((project) =>
            project.id === newData.id ? newData : project
          );
        }
        return [newData];
      },
      revalidate: false
    }
  );

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

  // Create node
  const { trigger: createFrontendNode } = useSWRMutation(
    'createNode',
    async (_, { arg }: { arg: FrontendNodeCreate }) => {
      return await createNode(session?.APIToken?.accessToken || '', arg);
    },
    {
      populateCache: (newNode) => {
        return [...frontendNodes, newNode];
      },
      revalidate: false
    }
  );

  // Delete node
  const { trigger: deleteNodeTrigger } = useSWRMutation(
    'deleteNode',
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

  // Set selected project
  const setSelectedProject = (project: Project | null) => {
    mutateSelectedProject(project, { revalidate: false });
  };

  // Update selected project and sync with projects list
  const updateBothSelectedAndProjectsList = async (data: ProjectUpdate) => {
    if (!selectedProject) return;

    const updatedProject = await updateSelectedProject({
      data
    });

    // Update both the selected project and the projects list
    mutateSelectedProject(updatedProject, { revalidate: false });
    
    // Also refresh the nodes since the project data has changed
    // This ensures nodes are updated when datasets/analyses are added/removed from the project
    mutateNodes();
  };

  // Add dataset to project and create corresponding node
  const addDatasetToProject = async (jobId: string) => {
    if (!selectedProject) return;

    // First create the node for the dataset
    await createFrontendNode({
      projectId: selectedProject.id,
      xPosition: -300.0,
      yPosition: 0.0,
      type: "dataset",
      datasetId: jobId,
      analysisId: null,
      automationId: null,
    });

    // Then update the project to include the dataset
    await updateBothSelectedAndProjectsList({
      type: "dataset",
      id: jobId,
      remove: false,
    });

    
  };

  // Remove dataset from project and delete corresponding node
  const removeDatasetFromProject = async (jobId: string) => {
    if (!selectedProject) return;

    // First update the project to remove the dataset
    await updateBothSelectedAndProjectsList({
      type: "dataset",
      id: jobId,
      remove: true,
    });

    // Then find and delete the corresponding node
    const nodeToDelete = frontendNodes?.find(node => node.datasetId === jobId);
    if (nodeToDelete) {
      await deleteNodeTrigger(nodeToDelete.id);
    }
  };

  return {
    projects,
    selectedProject,
    frontendNodes,
    error: error || nodesError,
    isLoading: isLoading || nodesLoading,
    createNewProject,
    updateBothSelectedAndProjectsList,
    setSelectedProject,
    updatePosition,
    createFrontendNode,
    deleteNodeTrigger,
    addDatasetToProject,
    removeDatasetFromProject,
  };
};
