'use client';

import Image from 'next/image';
import Link from 'next/link';
import { Database, BarChart, Bot } from 'lucide-react';
import { useState } from 'react';
import JobsOverview from './jobsOverview';
import { JobMetadata } from '../types/jobs';
import { getStatusColor } from '../lib/utils';



interface UserHeaderProps {
	analysisJobs: JobMetadata[];
	automationJobs: JobMetadata[];
	integrationJobs: JobMetadata[];
}

export default function UserHeader({ 
	analysisJobs,	
	automationJobs,
	integrationJobs,

}: UserHeaderProps) {
	const [isJobsOverviewOpen, setIsJobsOverviewOpen] = useState(false);

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
								className={`${getStatusColor("")} hover:opacity-80`}
								onClick={() => setIsJobsOverviewOpen(true)}
							>
								<Database size={20} />
							</button>
							<button className={`${getStatusColor("")} hover:opacity-80`}>
								<BarChart size={20} />
							</button>
							<button className={`${getStatusColor("")} hover:opacity-80`}>
								<Bot size={20} />
							</button>
						</div>
					</div>
				</div>
			</header>
			
			<JobsOverview 
				job_type="Integration"
				isOpen={isJobsOverviewOpen}
				onClose={() => setIsJobsOverviewOpen(false)}
				jobs={integrationJobs}
			/>
		</>
	);
} 