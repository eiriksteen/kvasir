'use client';

import Image from 'next/image';
import Link from 'next/link';
import JobsOverview from '@/components/JobsOverview';
import { Database, BarChart, Bot } from 'lucide-react';
import { useState } from 'react';
import { Job } from '../types/jobs';
import { getStatusColor } from '../lib/utils';
import { useSession } from 'next-auth/react';
import { useJobs } from '@/hooks';
import { redirect } from 'next/navigation';



export default function UserHeader() {

	const [integrationJobsIsOpen, setIntegrationJobsIsOpen] = useState(false);
	const [analysisJobsIsOpen, setAnalysisJobsIsOpen] = useState(false);
	const [automationJobsIsOpen, setAutomationJobsIsOpen] = useState(false);
	const { data: session } = useSession();

	if (!session) {
		redirect("/login");
	}

	const { jobs, jobState } = useJobs();
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
								className={`${getStatusColor(jobState.integrationState)} hover:opacity-80 ${jobState.integrationState === 'running' ? 'animate-pulse-running' : ''}`}
								onClick={() => setIntegrationJobsIsOpen(true)}>
								<Database size={20} />
							</button>
							<button 
								className={`${getStatusColor(jobState.analysisState)} hover:opacity-80 ${jobState.analysisState === 'running' ? 'animate-pulse-running' : ''}`}
								onClick={() => setAnalysisJobsIsOpen(true)}>
								<BarChart size={20} />
							</button>
							<button 
								className={`${getStatusColor(jobState.automationState)} hover:opacity-80 ${jobState.automationState === 'running' ? 'animate-pulse-running' : ''}`}
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