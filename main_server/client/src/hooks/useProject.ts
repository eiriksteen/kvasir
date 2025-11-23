import { 
  Project, 
  ProjectCreate, 
} from "@/types/api/project";
import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { useMemo } from "react";
import { UUID } from "crypto";
import { snakeToCamelKeys, camelToSnakeKeys } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchProjects(token: string): Promise<Project[]> {
  const response = await fetch(`${API_URL}/project/projects`, {
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
  const response = await fetch(`${API_URL}/project/project`, {
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


async function updateProjectViewPort(token: string, projectId: UUID, viewPortX: number, viewPortY: number, zoom: number): Promise<Project> {
  const response = await fetch(`${API_URL}/project/project/${projectId}/view-port`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys({ viewPortX, viewPortY, zoom }))
  });
  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to update project view port', errorText);
    throw new Error(`Failed to update project view port: ${response.status} ${errorText}`);
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

  const { trigger: triggerUpdateProjectViewPort } = useSWRMutation(
    "projects",
    async (_, { arg }: { arg: { projectId: UUID; viewPortX: number; viewPortY: number; zoom: number } }) => {
      const updatedProject = await updateProjectViewPort(session ? session.APIToken.accessToken : "", arg.projectId, arg.viewPortX, arg.viewPortY, arg.zoom);
      return updatedProject;
    },
    {
      populateCache: (updatedProject: Project) => {
        if (projects) {
          return projects.map(p => p.id === updatedProject.id ? updatedProject : p);
        }
        return [updatedProject];
      },
      revalidate: false
    }
  );

  return { projects, mutateProjects, error, isLoading, triggerCreateNewProject, triggerUpdateProjectViewPort };
}

export const useProject = (projectId?: UUID) => {
  const { projects, mutateProjects, triggerUpdateProjectViewPort } = useProjects();

  // Store selected project
  const project = useMemo(() => projects.find(project => project.id === projectId), [projects, projectId]);

  return {
    project,
    error: null,
    isLoading: !project,
    mutateProject: mutateProjects,
    triggerUpdateProjectViewPort,
  };
};
