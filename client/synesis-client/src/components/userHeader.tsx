'use client';

import Image from 'next/image';
import Link from 'next/link';
import JobsOverview from './jobsOverview';
import { Database, BarChart, Bot } from 'lucide-react';
import { use, useState } from 'react';
import { Job } from '../types/jobs';
import { getStatusColor } from '../lib/utils';
import { useSession } from 'next-auth/react';
import { useJobs } from '@/hooks/apiHooks';
import { redirect } from 'next/navigation';
import { useMonitorRunningJobs } from '@/hooks/apiHooks';
import { useJobStates } from '@/hooks/useJobStates';
interface UserHeaderProps {
	addedJobs: Job[];
	setAddedJobs: (addedJobs: Job[]) => void;
}

export default function UserHeader({ 
	addedJobs,
	setAddedJobs
}: UserHeaderProps) {


	const [integrationJobsIsOpen, setIntegrationJobsIsOpen] = useState(false);
	const [analysisJobsIsOpen, setAnalysisJobsIsOpen] = useState(false);
	const [automationJobsIsOpen, setAutomationJobsIsOpen] = useState(false);
	const { data: session } = useSession();

	if (!session) {
		redirect("/login");
	}

	const { jobs } = useJobs();

	useMonitorRunningJobs(addedJobs, setAddedJobs);

	const { integrationState, analysisState, automationState } = useJobStates(addedJobs);

	const integrationJobs = jobs?.filter((job: Job) => job.type === "integration");
	const analysisJobs = jobs?.filter((job: Job) => job.type === "analysis");
	const automationJobs = jobs?.filter((job: Job) => job.type === "automation");

	return (
		<>
			<header className="fixed top-0 left-0 right-0 z-50 bg-black">
				<div className="mx-auto px-4 sm:px-6 lg:px-6">
					<div className="flex items-center justify-between h-12">
						<Link href="/">
							<div className="relative w-[30px] h-[30px]">
								<Image
									src="/miyaicon.png"
									alt="Miya logo"
									fill
									priority
									className="object-contain"
								/>
							</div>
						</Link>
						
						<div className="flex items-center space-x-4">
							<button 
								className={`${getStatusColor(integrationState)} hover:opacity-80 ${integrationState === 'running' ? 'animate-pulse-running' : ''}`}
								onClick={() => setIntegrationJobsIsOpen(true)}>
								<Database size={20} />
							</button>
							<button 
								className={`${getStatusColor(analysisState)} hover:opacity-80 ${analysisState === 'running' ? 'animate-pulse-running' : ''}`}
								onClick={() => setAnalysisJobsIsOpen(true)}>
								<BarChart size={20} />
							</button>
							<button 
								className={`${getStatusColor(automationState)} hover:opacity-80 ${automationState === 'running' ? 'animate-pulse-running' : ''}`}
								onClick={() => setAutomationJobsIsOpen(true)}>
								<Bot size={20} />
							</button>
						</div>
					</div>
				</div>
			</header>
			
			<JobsOverview 
				job_type="Integration"
				isOpen={integrationJobsIsOpen}
				onClose={() => setIntegrationJobsIsOpen(false)}
				jobs={integrationJobs || []}
			/>
			<JobsOverview 
				job_type="Analysis"
				isOpen={analysisJobsIsOpen}
				onClose={() => setAnalysisJobsIsOpen(false)}
				jobs={analysisJobs || []}
			/>
			<JobsOverview 
				job_type="Automation"
				isOpen={automationJobsIsOpen}
				onClose={() => setAutomationJobsIsOpen(false)}
				jobs={automationJobs || []}
			/>
			
		</>
	);
} 