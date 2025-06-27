export interface Modality {
  id: string;
  name: string;
  description?: string;
}

export interface Task {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface Source {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface ProgrammingLanguage {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface ProgrammingLanguageVersion {
  id: string;
  programming_language_id: string;
  version: string;
  created_at: string;
}

export interface Model {
  id: string;
  name: string;
  description: string;
  input_description: string;
  output_description: string;
  config_parameters: string[];
  created_at: string;
  public: boolean;
  modality: Modality;
  source: Source;
  programming_language_version: ProgrammingLanguageVersion;
  tasks: Task[];
}

export interface ModelIntegrationMessage {
  id: string;
  job_id: string;
  content: string;
  stage: 'setup' | 'analysis' | 'planning' | 'training' | 'inference';
  type: 'tool_call' | 'result';
  current_task?: 'classification' | 'regression' | 'segmentation' | 'forecasting';
  created_at: string;
} 