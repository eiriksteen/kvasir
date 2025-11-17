import { 
  Project, 
  ProjectCreate, 
  ProjectDetailsUpdate, 
  AddEntityToProject, 
  RemoveEntityFromProject,
  UpdateNodePosition,
  EntityType
} from "@/types/project";
import { GraphNode, PipelineGraphNode } from "@/types/entity-graph";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { useCallback, useMemo } from "react";
import { UUID } from "crypto";
import { snakeToCamelKeys, camelToSnakeKeys } from "@/lib/utils";

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

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function createProject(token: string, projectData: ProjectCreate): Promise<Project> {
  const response = await fetch(`${API_URL}/project/create-project`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(projectData))
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to create project', errorText);
    throw new Error(`Failed to create project: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function updateProjectDetails(token: string, projectId: string, projectData: ProjectDetailsUpdate): Promise<Project> {
  const response = await fetch(`${API_URL}/project/update-project/${projectId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(projectData))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to update project details: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function addEntityToProject(token: string, entityData: AddEntityToProject): Promise<Project> {
  const response = await fetch(`${API_URL}/project/add-entity`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(entityData))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to add entity to project: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function removeEntityFromProject(token: string, entityData: RemoveEntityFromProject): Promise<Project> {
  const response = await fetch(`${API_URL}/project/remove-entity`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(entityData))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to remove entity from project: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function updateNodePosition(token: string, positionData: UpdateNodePosition): Promise<Project> {
  const response = await fetch(`${API_URL}/project/update-node-position`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(positionData))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to update node position: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function updateProjectViewport(token: string, viewportData: { projectId: UUID; x: number; y: number; zoom: number }): Promise<Project> {
  const response = await fetch(`${API_URL}/project/update-project-viewport`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(viewportData))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to update project viewport: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
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

export const useProject = (projectId?: UUID) => {
  const { data: session } = useSession();

  // TODO: Should not need to mutate all projects when just one changes
  const { projects, mutateProjects, triggerUpdateProject } = useProjects();

  // Store selected project
  const project = useMemo(() => projects.find(project => project.id === projectId), [projects, projectId]);

  // Update node position
  const { trigger: updatePosition } = useSWRMutation(
    "projects",
    async (_, { arg }: { arg: { projectId: UUID, entityType: EntityType, entityId: UUID, xPosition: number, yPosition: number } }) => {
      if (!project) return projects;

      await updateNodePosition(
        session?.APIToken?.accessToken || '',
        {
          projectId: arg.projectId,
          entityType: arg.entityType,
          entityId: arg.entityId,
          xPosition: arg.xPosition,
          yPosition: arg.yPosition
        }
      );

      // Optimistically update the project in the cache
      const updatedProjects = projects.map(p => {
        if (p.id !== project.id) return p;

        // Update the appropriate entity list in projectNodes
        switch (arg.entityType) {
          case "data_source":
            return {
              ...p,
              projectNodes: {
                ...p.projectNodes,
                projectDataSources: p.projectNodes.projectDataSources.map(ds => 
                  ds.dataSourceId === arg.entityId 
                    ? { ...ds, xPosition: arg.xPosition, yPosition: arg.yPosition }
                    : ds
                )
              }
            };
          case "dataset":
            return {
              ...p,
              projectNodes: {
                ...p.projectNodes,
                projectDatasets: p.projectNodes.projectDatasets.map(ds => 
                  ds.datasetId === arg.entityId 
                    ? { ...ds, xPosition: arg.xPosition, yPosition: arg.yPosition }
                    : ds
                )
              }
            };
          case "analysis":
            return {
              ...p,
              projectNodes: {
                ...p.projectNodes,
                projectAnalyses: p.projectNodes.projectAnalyses.map(a => 
                  a.analysisId === arg.entityId 
                    ? { ...a, xPosition: arg.xPosition, yPosition: arg.yPosition }
                    : a
                )
              }
            };
          case "pipeline":
            return {
              ...p,
              projectNodes: {
                ...p.projectNodes,
                projectPipelines: p.projectNodes.projectPipelines.map(pl => 
                  pl.pipelineId === arg.entityId 
                    ? { ...pl, xPosition: arg.xPosition, yPosition: arg.yPosition }
                    : pl
                )
              }
            };
          case "model_instantiated":
            return {
              ...p,
              projectNodes: {
                ...p.projectNodes,
                projectModelEntities: p.projectNodes.projectModelEntities.map(me => 
                  me.modelInstantiatedId === arg.entityId 
                    ? { ...me, xPosition: arg.xPosition, yPosition: arg.yPosition }
                    : me
                )
              }
            };
          default:
            return p;
        }
      });

      return updatedProjects;
    },
    {
      populateCache: (updatedProjects) => updatedProjects,
      revalidate: false
    }
  );

  const updateProjectAndNode = useCallback(async (data: ProjectDetailsUpdate) => {
    if (!project) return;
    await triggerUpdateProject({data, projectId: project.id});
  }, [project, triggerUpdateProject]);

  // Update project viewport
  const { trigger: updateProjectViewPort } = useSWRMutation(
    "projects",
    async (_, { arg }: { arg: { x: number; y: number; zoom: number } }) => {
      if (!project) return projects;

      await updateProjectViewport(
        session?.APIToken?.accessToken || '',
        {
          projectId: project.id,
          x: arg.x,
          y: arg.y,
          zoom: arg.zoom
        }
      );

      // Optimistically update the project in the cache
      const updatedProjects = projects.map(p => {
        if (p.id !== project.id) return p;
        return {
          ...p,
          viewPortX: arg.x,
          viewPortY: arg.y,
          viewPortZoom: arg.zoom
        };
      });

      return updatedProjects;
    },
    {
      populateCache: (updatedProjects) => updatedProjects,
      revalidate: false
    }
  );

  const calculateNodePosition = useCallback(() => {
    if (!project?.projectNodes || project.projectNodes.projectDataSources.length === 0) {
      return { x: -300, y: 0 };
    }

    const baseX = -300;
    const verticalSpacing = 75; 

    const yPositions = project.projectNodes.projectDataSources.map(ds => ds.yPosition);
    const highestY = Math.max(...yPositions);

    return { x: baseX, y: highestY + verticalSpacing };
  }, [project?.projectNodes]);

  // Unified function to add any entity to project
  const addEntity = async (
    entityType: "data_source" | "dataset" | "analysis" | "pipeline" | "model_instantiated", 
    entityId: UUID
  ) => {
    if (!project) return;

    // Update the project to include the entity
    await addEntityToProject(session?.APIToken?.accessToken || '', {
      projectId: project.id,
      entityType,
      entityId: entityId as UUID,
    });

    mutateProjects();
  };

  // Unified function to remove any entity from project
  const removeEntity = async (entityType: "data_source" | "dataset" | "analysis" | "pipeline" | "model_instantiated", entityId: UUID) => {
    if (!project) return;

    // Update the project to remove the entity
    await removeEntityFromProject(session?.APIToken?.accessToken || '', {
      projectId: project.id,
      entityType,
      entityId: entityId as UUID,
    });

    mutateProjects();
  };

  // Get GraphNode for a specific entity ID - provides access to inputs/outputs
  const getEntityGraphNode = useCallback((entityId: UUID): GraphNode | PipelineGraphNode | null => {
    if (!project?.graph) return null;

    // Search through all entity types in the graph
    const dataSource = project.graph.dataSources.find(ds => ds.id === entityId);
    if (dataSource) return dataSource;

    const dataset = project.graph.datasets.find(d => d.id === entityId);
    if (dataset) return dataset;

    const pipeline = project.graph.pipelines.find(p => p.id === entityId);
    if (pipeline) return pipeline;

    const analysis = project.graph.analyses.find(a => a.id === entityId);
    if (analysis) return analysis;

    const modelInstantiated = project.graph.modelsInstantiated.find(me => me.id === entityId);
    if (modelInstantiated) return modelInstantiated;

    return null;
  }, [project?.graph]);

  return {
    project,
    error: null,
    isLoading: !project,
    updateProjectAndNode,
    updatePosition,
    updateProjectViewPort,
    addEntity,
    removeEntity,
    calculateDatasetPosition: calculateNodePosition,
    mutateProject: mutateProjects,
    getEntityGraphNode,
  };
};
