import { Job } from "@/types/jobs";

export interface Modality {
  id: string;
  name: string;
  description?: string;
}

export interface Task {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
}

export interface Source {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
}

export interface ProgrammingLanguage {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
}

export interface ProgrammingLanguageVersion {
  id: string;
  programmingLanguageId: string;
  version: string;
  createdAt: string;
}

export interface Model {
  id: string;
  name: string;
  description: string;
  inputDescription: string;
  outputDescription: string;
  configParameters: string[];
  createdAt: string;
  public: boolean;
  modality: Modality;
  source: Source;
  programmingLanguageVersion: ProgrammingLanguageVersion;
  tasks: Task[];
  integrationJobs: Job[];
}

export interface ModelIntegrationMessage {
  id: string;
  jobId: string;
  content: string;
  stage: 'setup' | 'analysis' | 'planning' | 'training' | 'inference';
  type: 'tool_call' | 'result';
  currentTask?: 'classification' | 'regression' | 'segmentation' | 'forecasting';
  createdAt: string;
} 