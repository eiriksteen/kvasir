import useSWR from "swr";
import { ProjectGraph } from "@/types/orchestrator";
import { UUID } from "crypto";
import { snakeToCamelKeys } from "@/lib/utils";
import { useSession } from "next-auth/react";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchProjectGraph(token: string, projectId: string): Promise<ProjectGraph> {
    const response = await fetch(`${API_URL}/project/project-graph/${projectId}`, {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        const errorText = await response.text();
        console.error('Failed to fetch project graph', errorText);
        throw new Error(`Failed to fetch project graph: ${response.status} ${errorText}`);
    }

    const data = await response.json();
    return snakeToCamelKeys(data);
}


export const useProjectGraph = (projectId: UUID) => {
    const { data: session } = useSession();
    const { data: projectGraph, isLoading, error } = useSWR<ProjectGraph>(
        session ? ["project-graph", projectId] : null,
        () => fetchProjectGraph(session?.APIToken?.accessToken || '', projectId)
    );
    return { projectGraph, isLoading, error };
}