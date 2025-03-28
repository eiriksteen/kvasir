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
import { useMonitorJobs } from '@/hooks/apiHooks';

interface UserHeaderProps {
	integrationJobState: string;
	setIntegrationJobState: (jobState: string) => void;
	analysisJobState: string;
	setAnalysisJobState: (jobState: string) => void;
	automationJobState: string;
	setAutomationJobState: (jobState: string) => void;
}

export default function UserHeader({ 
	integrationJobState,
	setIntegrationJobState,
	analysisJobState,
	setAnalysisJobState,
	automationJobState,
	setAutomationJobState
}: UserHeaderProps) {


	const [integrationJobsIsOpen, setIntegrationJobsIsOpen] = useState(false);
	const [analysisJobsIsOpen, setAnalysisJobsIsOpen] = useState(false);
	const [automationJobsIsOpen, setAutomationJobsIsOpen] = useState(false);
	const { data: session } = useSession();

	if (!session) {
		redirect("/login");
	}

	const { jobs } = useJobs(session?.APIToken.accessToken);

	const { jobsInProgress: integrationJobsInProgress } = useMonitorJobs(
		integrationJobState,
		setIntegrationJobState,
		session?.APIToken.accessToken
	);
	const { jobsInProgress: analysisJobsInProgress } = useMonitorJobs(
		analysisJobState,
		setAnalysisJobState,
		session?.APIToken.accessToken
	);
	const { jobsInProgress: automationJobsInProgress } = useMonitorJobs(
		automationJobState,
		setAutomationJobState,
		session?.APIToken.accessToken
	);

	const integrationJobs = jobs?.filter((job: Job) => job.type === "integration");
	const analysisJobs = jobs?.filter((job: Job) => job.type === "analysis");
	const automationJobs = jobs?.filter((job: Job) => job.type === "automation");

	const onCloseJobsOverview = (
		oldState: string,
		setOpen: (open: boolean) => void, 
		setJobState: (jobState: string) => void) => {
			
		setOpen(false)
		if (oldState !== "running") {
			setJobState("")
		}
	}

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
								className={`${getStatusColor(integrationJobState)} hover:opacity-80`}
								onClick={() => setIntegrationJobsIsOpen(true)}>
								<Database size={20} />
							</button>
							<button 
								className={`${getStatusColor(analysisJobState)} hover:opacity-80`}
								onClick={() => setAnalysisJobsIsOpen(true)}>
								<BarChart size={20} />
							</button>
							<button 
								className={`${getStatusColor(automationJobState)} hover:opacity-80`}
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
				onClose={() => onCloseJobsOverview(integrationJobState, setIntegrationJobsIsOpen, setIntegrationJobState)}
				jobs={integrationJobs || []}
			/>
			<JobsOverview 
				job_type="Analysis"
				isOpen={analysisJobsIsOpen}
				onClose={() => onCloseJobsOverview(analysisJobState, setAnalysisJobsIsOpen, setAnalysisJobState)}
				jobs={analysisJobs || []}
			/>
			<JobsOverview 
				job_type="Automation"
				isOpen={automationJobsIsOpen}
				onClose={() => onCloseJobsOverview(automationJobState, setAutomationJobsIsOpen, setAutomationJobState)}
				jobs={automationJobs || []}
			/>
			
		</>
	);
} 