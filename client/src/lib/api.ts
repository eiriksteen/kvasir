import {EventSource} from 'eventsource'
import { Analysis } from "@/types/analysis";
import { ChatMessageAPI, Conversation } from "@/types/chat";
import { Datasets } from "@/types/datasets";
import { Job } from "@/types/jobs";
import { IntegrationAgentFeedback, IntegrationMessage } from "@/types/integration";
const API_URL = process.env.NEXT_PUBLIC_API_URL;
const WS_URL = process.env.NEXT_PUBLIC_WS_URL;

export async function fetchDatasets(token: string): Promise<Datasets> {

  const response = await fetch(`${API_URL}/ontology/datasets`, {
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

export async function postIntegrationJob(token: string, files: File[], description: string, dataSource: string): Promise<Job> {
  const formData = new FormData();
  files.forEach(file => {
    formData.append("files", file);
  });
  formData.append("data_description", description);
  formData.append("data_source", dataSource);

  const response = await fetch(`${API_URL}/integration/call-integration-agent`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to add dataset', errorText);
    throw new Error(`Failed to add dataset: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

export async function submitAnalysis(token: string, datasetId: string): Promise<Job> {
  const response = await fetch(`${API_URL}/eda/call-eda-agent?dataset_id=${datasetId}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error(JSON.stringify({ "dataset_id": datasetId }));
    console.error('Failed to do analysis', errorText);
    throw new Error(`Failed to do analysis: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

export async function fetchAnalysis(token: string, datasetId: string): Promise<Analysis> {
  const response = await fetch(`${API_URL}/eda/analysis-result/${datasetId}`, {
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

export async function fetchJobs(token: string, onlyRunning: boolean = false): Promise<Job[]> {
  const response = await fetch(`${API_URL}/jobs?only_running=${onlyRunning}`, {
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

export async function* streamChat(token: string, prompt: string, conversationId: string): AsyncGenerator<string> {
  const response = await fetch(`${API_URL}/chat/completions/${conversationId}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ "content": prompt })
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

export async function fetchMessages(token: string, conversationId: string): Promise<ChatMessageAPI[]> {
  const response = await fetch(`${API_URL}/chat/conversation/${conversationId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch messages', errorText);
    throw new Error(`Failed to fetch messages: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return data;
}

export async function postConversation(token: string): Promise<Conversation> {
  const response = await fetch(`${API_URL}/chat/conversation`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
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

export async function postChatContextUpdate(token: string, conversationId: string, datasetIds: string[], automationIds: string[]): Promise<string> {
  const response = await fetch(`${API_URL}/chat/context`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      "conversation_id": conversationId,
      "dataset_ids": datasetIds,
      "automation_ids": automationIds
    })
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to update context', errorText);
    throw new Error(`Failed to update context: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  
  return data;
}

export function createIntegrationSocket(jobId: string): WebSocket {
  const socket = new WebSocket(`${WS_URL}/integration/integration-agent-human-in-the-loop/${jobId}/ws`);
  return socket;
}

export function createIntegrationEventSource(token: string, jobId: string): EventSource {
  return new EventSource(`${API_URL}/integration/integration-agent-sse/${jobId}`,
    {
      fetch: (input, init) =>
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

export async function postIntegrationAgentFeedback(token: string, feedback: IntegrationAgentFeedback): Promise<IntegrationMessage> {

  const response = await fetch(`${API_URL}/integration/integration-agent-feedback`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(feedback)
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to post integration agent feedback', errorText);
    throw new Error(`Failed to post integration agent feedback: ${response.status} ${errorText}`);
  }

  return response.json();
} 

export async function postIntegrationAgentApprove(token: string, jobId: string): Promise<Job> {
  const response = await fetch(`${API_URL}/integration/integration-agent-approve/${jobId}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to approve integration agent', errorText);
    throw new Error(`Failed to approve integration agent: ${response.status} ${errorText}`);
  }

  return response.json();
}

export async function fetchIntegrationMessages(token: string, jobId: string): Promise<IntegrationMessage[]> {

  const response = await fetch(`${API_URL}/integration/integration-messages/${jobId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch integration messages', errorText);
    throw new Error(`Failed to fetch integration messages: ${response.status} ${errorText}`);
  }

  return response.json();
}