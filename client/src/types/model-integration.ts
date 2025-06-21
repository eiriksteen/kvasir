export interface ModelIntegration {
  id: string;
  name: string;
  source: 'github' | 'pip';
  url: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  startedAt: string;
  completedAt?: string;
  tasks: string[];
  modality: string;
}

export interface IntegrationStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  icon: React.ReactNode;
  duration?: string;
  details?: string;
}

export interface ModelIntegrationFormData {
  name: string;
  source: 'github' | 'pip';
  url: string;
  tasks: string[];
  modality: string;
} 