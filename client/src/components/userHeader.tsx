'use client';

import Image from 'next/image';
import Link from 'next/link';
import JobsOverview from '@/components/JobsOverview';
import IntegrationManager from '@/components/integration/IntegrationManager';
import { Database, BarChart, Bot, LogOut, FolderOpen, Settings } from 'lucide-react';
import { useState } from 'react';
import { getStatusColor } from '../lib/utils';
import { useSession } from "next-auth/react";
import { useJobs, useProject } from '@/hooks';
import { redirect } from 'next/navigation';

export default function UserHeader() {
	const [integrationJobsIsOpen, setIntegrationJobsIsOpen] = useState(false);
	const [analysisJobsIsOpen, setAnalysisJobsIsOpen] = useState(false);
	const [automationJobsIsOpen, setAutomationJobsIsOpen] = useState(false);
	const [datasetsIsOpen, setDatasetsIsOpen] = useState(false);
	const { data: session } = useSession();
	const { setSelectedProject } = useProject();

	if (!session) {
		redirect("/login");
	}

	// const { jobs: integrationJobs, jobState: integrationJobState } = useJobs("integration");
	const { jobState: integrationJobState } = useJobs("integration");
	const { jobs: analysisJobs, jobState: analysisJobState } = useJobs("analysis");
	const { jobs: automationJobs, jobState: automationJobState } = useJobs("automation");

	const handleExit = () => {
		setSelectedProject(null);
	};

	return (
		<>
			<header className="fixed top-0 left-0 right-0 z-50 bg-black">
				<div className="mx-auto px-4 sm:px-6 lg:px-6">
					<div className="flex items-center justify-between h-12">
						<div className="flex items-center space-x-4">
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
							<button 
								className="text-zinc-400 hover:text-zinc-200 transition-colors"
								onClick={handleExit}
								title="Exit to Project Selection"
							>
								<LogOut size={20} />
							</button>
							<button 
								className="text-zinc-400 hover:text-zinc-200 transition-colors"
								onClick={() => setDatasetsIsOpen(true)}
								title="Manage Datasets"
							>
								<FolderOpen size={20} />
							</button>
							<button 
								// className={`${getStatusColor(integrationJobState)} hover:opacity-80 ${integrationJobState.integrationState === 'running' ? 'animate-pulse-running' : ''}`}
								// TODO: Fix className for integrationJobState - structure might differ now?
								className={`${getStatusColor(integrationJobState)} hover:opacity-80 ${integrationJobState === 'running' ? 'animate-pulse-running' : ''}`} 
								onClick={() => setIntegrationJobsIsOpen(true)}>
								<Database size={20} />
							</button>
						</div>
						
						<div className="flex items-center space-x-4">
							<button 
								className={`${getStatusColor(analysisJobState)} hover:opacity-80 ${analysisJobState === 'running' ? 'animate-pulse-running' : ''}`}
								onClick={() => setAnalysisJobsIsOpen(true)}>
								<BarChart size={20} />
							</button>
							<button 
								className={`${getStatusColor(automationJobState)} hover:opacity-80 ${automationJobState === 'running' ? 'animate-pulse-running' : ''}`}
								onClick={() => setAutomationJobsIsOpen(true)}>
								<Bot size={20} />
							</button>
							<button 
								className="text-zinc-400 hover:text-zinc-200 transition-colors"
								onClick={() => {
									// TODO: Implement settings
								}}>
								<Settings size={20} />
							</button>
						</div>
					</div>
				</div>
			</header>
			
			<IntegrationManager 
				isOpen={datasetsIsOpen}
				onClose={() => setDatasetsIsOpen(false)}
			/>
			<IntegrationManager 
				isOpen={integrationJobsIsOpen}
				onClose={() => setIntegrationJobsIsOpen(false)}
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