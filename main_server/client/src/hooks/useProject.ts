import { 
  Project, 
  ProjectCreate, 
  ProjectDetailsUpdate, 
  AddEntityToProject, 
  RemoveEntityFromProject,
  UpdateEntityPosition 
} from "@/types/project";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { useCallback, useMemo } from "react";
import { UUID } from "crypto";
import { snakeToCamelKeys, camelToSnakeKeys } from "@/lib/utils";

type EntityType = "data_source" | "dataset" | "analysis" | "pipeline" | "model_entity";

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

async function updateEntityPosition(token: string, positionData: UpdateEntityPosition): Promise<Project> {
  const response = await fetch(`${API_URL}/project/update-entity-position`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(positionData))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to update entity position: ${response.status} ${errorText}`);
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

export const useProject = (projectId: UUID) => {
  const { data: session } = useSession();

  // TODO: Should not need to mutate all projects when just one changes
  const { projects, mutateProjects, triggerUpdateProject } = useProjects();

  // Store selected project
  const project = useMemo(() => projects.find(project => project.id === projectId), [projects, projectId]);

  // Update entity position
  const { trigger: updatePosition } = useSWRMutation(
    "projects",
    async (_, { arg }: { arg: { entityType: EntityType, entityId: UUID, xPosition: number, yPosition: number } }) => {
      if (!project) return projects;

      await updateEntityPosition(
        session?.APIToken?.accessToken || '',
        {
          projectId: project.id,
          entityType: arg.entityType,
          entityId: arg.entityId,
          xPosition: arg.xPosition,
          yPosition: arg.yPosition
        }
      );

      // Optimistically update the project in the cache
      const updatedProjects = projects.map(p => {
        if (p.id !== project.id) return p;

        // Update the appropriate entity list in the graph
        switch (arg.entityType) {
          case "data_source":
            return {
              ...p,
              graph: {
                ...p.graph,
                dataSources: p.graph.dataSources.map(ds => 
                  ds.id === arg.entityId 
                    ? { ...ds, xPosition: arg.xPosition, yPosition: arg.yPosition }
                    : ds
                )
              }
            };
          case "dataset":
            return {
              ...p,
              graph: {
                ...p.graph,
                datasets: p.graph.datasets.map(ds => 
                  ds.id === arg.entityId 
                    ? { ...ds, xPosition: arg.xPosition, yPosition: arg.yPosition }
                    : ds
                )
              }
            };
          case "analysis":
            return {
              ...p,
              graph: {
                ...p.graph,
                analyses: p.graph.analyses.map(a => 
                  a.id === arg.entityId 
                    ? { ...a, xPosition: arg.xPosition, yPosition: arg.yPosition }
                    : a
                )
              }
            };
          case "pipeline":
            return {
              ...p,
              graph: {
                ...p.graph,
                pipelines: p.graph.pipelines.map(pl => 
                  pl.id === arg.entityId 
                    ? { ...pl, xPosition: arg.xPosition, yPosition: arg.yPosition }
                    : pl
                )
              }
            };
          case "model_entity":
            return {
              ...p,
              graph: {
                ...p.graph,
                modelEntities: p.graph.modelEntities.map(me => 
                  me.id === arg.entityId 
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
    if (!project?.graph || project.graph.dataSources.length === 0) {
      return { x: -300, y: 0 };
    }

    const baseX = -300;
    const verticalSpacing = 75; 

    const yPositions = project.graph.dataSources.map(ds => ds.yPosition);
    const highestY = Math.max(...yPositions);

    return { x: baseX, y: highestY + verticalSpacing };
  }, [project?.graph]);

  // Unified function to add any entity to project
  const addEntity = async (
    entityType: "data_source" | "dataset" | "analysis" | "pipeline" | "model_entity", 
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
  const removeEntity = async (entityType: "data_source" | "dataset" | "analysis" | "pipeline" | "model_entity", entityId: UUID) => {
    if (!project) return;

    // Update the project to remove the entity
    await removeEntityFromProject(session?.APIToken?.accessToken || '', {
      projectId: project.id,
      entityType,
      entityId: entityId as UUID,
    });

    mutateProjects();
  };

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
  };
};
