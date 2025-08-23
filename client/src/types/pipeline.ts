import { Run } from "@/types/runs";


export interface Pipeline {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  updatedAt: string;
} 

export interface Function {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  updatedAt: string;
}

export interface Modality {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Task {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Source {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
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
  updatedAt: string;
}

export interface Model {
  id: string;
  name: string;
  description: string;
  inputDescription: string;
  outputDescription: string;
  configParameters: string[];
  public: boolean;
  modality: Modality;
  source: Source;
  programmingLanguageVersion: ProgrammingLanguageVersion;
  tasks: Task[];
  integrationJobs: Run[];
  createdAt: string;
  updatedAt: string;
}