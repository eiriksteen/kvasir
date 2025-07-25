export interface Job {
	id: string;
	jobName: string;
	type: string;
	status: string;
	conversationId: string | null;
	startedAt: string;
	completedAt: string | null;
}

