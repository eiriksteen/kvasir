import { EventSource } from 'eventsource';
import { Conversation, ConversationCreate, Prompt } from "@/types/chat";
import { Dataset, DatasetWithObjectLists } from "@/types/data-objects";
import { Analyses } from "@/types/analysis";
import { Job } from "@/types/jobs";
import { Project, ProjectCreate, ProjectUpdate } from "@/types/project";
import { AnalysisRequest } from "@/types/analysis";
import { FrontendNode, FrontendNodeCreate } from "@/types/node";
import { Model } from "@/types/automation";
import { DataSource, FileDataSource } from '@/types/data-integration';

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const WS_URL = process.env.NEXT_PUBLIC_WS_URL;

export async function fetchDatasets(token: string): Promise<Dataset[]> {

  const response = await fetch(`${API_URL}/data-objects/datasets?include_integration_jobs=1&include_object_lists=0`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch datasets', errorText);
    throw new Error(`Failed to fetch datasets: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

export async function fetchDatasetsWithObjectLists(token: string): Promise<DatasetWithObjectLists[]> {
  const response = await fetch(`${API_URL}/data-objects/datasets?include_integration_jobs=1&include_object_lists=1`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch datasets with object lists', errorText);
    throw new Error(`Failed to fetch datasets with object lists: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

export async function postAnalysisPlanner(token: string, analysisRequest: AnalysisRequest): Promise<Job> {
  const response = await fetch(`${API_URL}/analysis/create-analysis`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(analysisRequest)
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to run analysis planner: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

export async function deleteAnalysisJobResultsDB(token: string, jobId: string): Promise<void> {
  const response = await fetch(`${API_URL}/analysis/delete-analysis-job-results/${jobId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to delete analysis job results: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

export async function postAnalysis(token: string, datasetIds: string[], automationIds: string[]): Promise<Job> {
  const response = await fetch(`${API_URL}/eda/call-eda-agent?dataset_ids=${datasetIds.join(",")}&automation_ids=${automationIds.join(",")}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to do analysis: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

export async function fetchAnalysisJobResults(token: string): Promise<Analyses> {
  const response = await fetch(`${API_URL}/analysis/analysis-job-results`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text()
    console.error('Failed to fetch analysis', errorText);
    throw new Error(`Failed to fetch analysis: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

export async function fetchJobs(token: string, onlyRunning: boolean = false, type: string | null = null): Promise<Job[]> {
  const response = await fetch(`${API_URL}/jobs?only_running=${onlyRunning}&type=${type}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch jobs', errorText);
    throw new Error(`Failed to fetch jobs: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
} 

export async function fetchJobsBatch(token: string, jobIds: string[]): Promise<Job[]> {
  const response = await fetch(`${API_URL}/jobs/batch`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(jobIds)
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch jobs', errorText);
    throw new Error(`Failed to fetch jobs: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

export async function fetchJob(token: string, jobId: string): Promise<Job> {
  const response = await fetch(`${API_URL}/jobs/${jobId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch job', errorText);
    throw new Error(`Failed to fetch job: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

export async function* streamChat(token: string, prompt: Prompt): AsyncGenerator<string> {
  const response = await fetch(`${API_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(prompt)
  });

  const reader = response.body?.getReader();
  if (!reader) return;
  const decoder = new TextDecoder();
  
  while (true) {
    const result = await reader.read();
    if (result.done) break;
    const text = decoder.decode(result.value);
    yield text;
  }
}

export async function postConversation(token: string, conversationData: ConversationCreate): Promise<Conversation> {

  const response = await fetch(`${API_URL}/chat/conversation`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(conversationData)
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to create conversation', errorText);
    throw new Error(`Failed to create conversation: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

export async function fetchConversations(token: string): Promise<Conversation[]> {
  const response = await fetch(`${API_URL}/chat/conversations`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to get conversations', errorText);
    throw new Error(`Failed to get conversations: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

export function createAnalysisEventSource(token: string, jobId: string): EventSource {
  return new EventSource(`${API_URL}/analysis/analysis-agent-sse/${jobId}`,
    {
      fetch: (input: RequestInfo | URL, init?: RequestInit) =>
        fetch(input, {
          ...init,
          headers: {
            ...init?.headers,
            Authorization: `Bearer ${token}`,
          },
        }),
    }
  );
}

export function createJobEventSource(token: string, jobType: string): EventSource {
  return new EventSource(`${API_URL}/jobs-sse?job_type=${jobType}`, {
    fetch: (input, init) =>
      fetch(input, {
        ...init,
        headers: {
          ...init?.headers,
          Authorization: `Bearer ${token}`,
        },
      }),
  });
}


export async function fetchProjects(token: string): Promise<Project[]> {
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

export async function createProject(token: string, projectData: ProjectCreate): Promise<Project> {
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

export async function updateProject(token: string, projectId: string, projectData: ProjectUpdate): Promise<Project> {
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
    throw new Error(`Failed to update project: ${response.status} ${errorText}`);
  }

  return response.json();
}

export async function fetchProjectNodes(token: string, projectId: string): Promise<FrontendNode[]> {
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

export async function updateNodePosition(token: string, node: FrontendNode): Promise<FrontendNode> {
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

export async function createNode(token: string, node: FrontendNodeCreate): Promise<FrontendNode> {
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

export async function deleteNode(token: string, nodeId: string): Promise<string> {
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

export async function fetchModels(token: string, only_owned: boolean = false): Promise<Model[]> {

  const route = only_owned  ? "/automation/models/my?include_integration_jobs=1" : "/automation/models?include_integration_jobs=1";
  const response = await fetch(`${API_URL}${route}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch models', errorText);
    throw new Error(`Failed to fetch models: ${response.status} ${errorText}`);
  }

  return response.json();
}

export async function getDataIntegrationJobResults(token: string, jobId: string): Promise<{ jobId: string; datasetId: string }> {
  const response = await fetch(`${API_URL}/data-integration/integration-job-results/${jobId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to get integration job results', errorText);
    throw new Error(`Failed to get integration job results: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

export async function fetchDataSources(token: string): Promise<DataSource[]> {
  const response = await fetch(`${API_URL}/data-integration/data-sources`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch data sources', errorText);
    throw new Error(`Failed to fetch data sources: ${response.status} ${errorText}`);
  }

  return response.json();
}

export async function createFileDataSource(token: string, files: File[]): Promise<FileDataSource> {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));

  const response = await fetch(`${API_URL}/data-integration/file-data-sources`, {
    // FormData post with files
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to create file data source', errorText);
    throw new Error(`Failed to create file data source: ${response.status} ${errorText}`);
  }

  return response.json();
}