export type IntegrationMessage = {
  id: string;
  jobId: string;
  content: string;
  role: string;
  type: string;
};

export type IntegrationAgentFeedback = {
  jobId: string;
  content: string;
};