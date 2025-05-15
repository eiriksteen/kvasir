
export type IntegrationMessage = {
  id: string;
  job_id: string;
  content: string;
  role: string;
  type: string;
};

export type IntegrationAgentFeedback = {
  job_id: string;
  content: string;
};