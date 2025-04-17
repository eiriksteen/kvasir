import { ChatMessageAPI, Conversation } from "@/types/chat";
import { Datasets } from "@/types/datasets";
import { Job } from "@/types/jobs";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

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

export async function postDataset(token: string, file: File, description: string): Promise<Job> {

  const formData = new FormData();
  formData.append("file", file);
  formData.append("data_description", description);

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