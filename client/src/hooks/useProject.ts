import { fetchProjects, createProject, updateProject } from "@/lib/api";
import { Project, ProjectCreate, ProjectUpdate } from "@/types/project";
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
  const { trigger: updateExistingProject } = useSWRMutation(
    "projects",
    async (_, { arg }: { arg: { projectId: string; data: ProjectUpdate } }) => {
      const updatedProject = await updateProject(
        session ? session.APIToken.accessToken : "",
        arg.projectId,
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

  // Set selected project
  const setSelectedProject = (project: Project | null) => {
    mutateSelectedProject(project, { revalidate: false });
  };

  // Update selected project and sync with projects list
  const updateSelectedProject = async (data: ProjectUpdate) => {
    if (!selectedProject) return;

    const updatedProject = await updateExistingProject({
      projectId: selectedProject.id,
      data
    });

    // Update both the selected project and the projects list
    mutateSelectedProject(updatedProject, { revalidate: false });
  };

  return {
    projects,
    selectedProject,
    error,
    isLoading,
    createNewProject,
    updateExistingProject,
    setSelectedProject,
    updateSelectedProject
  };
};
