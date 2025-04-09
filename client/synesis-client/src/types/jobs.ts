export interface Job {
	id: string;
	type: string;
	status: string;
	startedAt: string;
	completedAt: string | null;
}

