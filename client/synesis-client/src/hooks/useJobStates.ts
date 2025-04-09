import { useMemo } from 'react';
import { Job } from '@/types/jobs';

export const useJobStates = (jobs: Job[]) => {
    return useMemo(() => {
        const states: { [key: string]: string } = {
            integration: "",
            analysis: "",
            automation: ""
        };

        const getCategoryState = (categoryJobs: Job[]) => {
            if (categoryJobs.some(job => job.status === 'running')) return 'running';
            if (categoryJobs.some(job => job.status === 'failed')) return 'failed';
            if (categoryJobs.some(job => job.status === 'completed')) return 'completed';
            return '';
        };

        for (const category of Object.keys(states)) {
            const categoryJobs = jobs.filter(job => job.type === category);
            states[category] = getCategoryState(categoryJobs);
        }

        return {
            integrationState: states.integration,
            analysisState: states.analysis,
            automationState: states.automation
        };
    }, [jobs]);
}; 