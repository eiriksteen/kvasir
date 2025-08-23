'use client';

import Image from 'next/image';
import Link from 'next/link';
import { Database, ChevronDown } from 'lucide-react';
import { useSession } from "next-auth/react";
import { useProjects, useProject } from '@/hooks';
import { redirect, useRouter } from 'next/navigation';
import { useState, useRef, useEffect } from 'react';
import { Project } from '@/types/project';
import { UUID } from 'crypto';

interface UserHeaderProps {
	projectId: UUID | undefined;
} 

export default function UserHeader({ projectId }: UserHeaderProps) {
	const { data: session } = useSession();
	const { projects } = useProjects();
	const { project } = useProject(projectId || '');
	const [showProjectDropdown, setShowProjectDropdown] = useState(false);
	const dropdownRef = useRef<HTMLDivElement>(null);
	const router = useRouter();

	if (!session) {
		redirect("/login");
	}

	useEffect(() => {
		const handleClickOutside = (event: MouseEvent) => {
			if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
				setShowProjectDropdown(false);
			}
		};

		document.addEventListener('mousedown', handleClickOutside);
		return () => {
			document.removeEventListener('mousedown', handleClickOutside);
		};
	}, []);

	const handleProjectSelect = (project: Project) => {
		router.push(`/projects/${project.id}`);
		setShowProjectDropdown(false);
	};

	const handleBackToMenu = () => {
		setShowProjectDropdown(false);
		router.push('/projects');
	};

	return (
		<header className="fixed top-0 left-0 right-0 z-50 bg-black">
			<div className="mx-auto px-4 sm:px-6 lg:pr-3">
				<div className="flex items-center justify-between h-12">
					{/* Logo and Project Title on the left */}
					<div className="flex items-center space-x-4">
						<Link href="/projects">
							<div className="relative w-[25px] h-[25px]">
								<Image
									src="/miyaicon.png"
									alt="Miya logo"
									fill
									priority
									className="object-contain"
								/>
							</div>
						</Link>
						
						{/* Project Title with Slash */}
						{project && (
							<div className="flex items-center space-x-3">
								<div className="text-zinc-500 text-lg font-light">/</div>
								<div className="flex flex-col">
									<div className="text-zinc-300 text-sm font-medium">
										{project.name}
									</div>
									{project.description && (
										<div className="text-zinc-500 text-xs truncate max-w-[200px]">
											{project.description}
										</div>
									)}
								</div>
							</div>
						)}
					</div>
					
					{/* Three buttons on the right */}
					<div className="flex items-center gap-2">
						<div className="relative" ref={dropdownRef}>
							<button
								onClick={() => setShowProjectDropdown(!showProjectDropdown)}
								className="text-zinc-400 hover:text-zinc-200 transition-colors px-3 py-1 rounded-md border border-zinc-700 hover:border-zinc-600 flex items-center space-x-1"
								title="Select Project"
							>
								<span className="text-sm font-medium">
									Projects
								</span>
								<ChevronDown size={14} className={`transition-transform ${showProjectDropdown ? 'rotate-180' : ''}`} />
							</button>
							
							{/* Project Dropdown */}
							{showProjectDropdown && (
								<div className="absolute top-full right-0 mt-1 w-64 bg-zinc-900 border border-zinc-800 rounded-lg shadow-lg z-50">
									<div className="p-2">
										{/* Projects List */}
										<div className="max-h-48 overflow-y-auto">
											{projects?.slice().reverse().map((project) => (
												<button
													key={project.id}
													onClick={() => handleProjectSelect(project)}
													className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors ${
														project.id === projectId
															? 'bg-zinc-700 text-zinc-200'
															: 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800'
													}`}
												>
													<div className="font-medium">{project.name}</div>
													{project.description && (
														<div className="text-xs text-zinc-500 mt-1 truncate">
															{project.description}
														</div>
													)}
												</button>
											))}
										</div>
										
										{/* Divider */}
										<div className="border-t border-zinc-800 mt-1 mb-1"></div>
										
										{/* Back to Menu Button */}
										<button
											onClick={handleBackToMenu}
											className="w-full text-left px-3 py-1.5 text-xs text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50 rounded transition-colors font-medium"
										>
											← Back to Menu
										</button>
									</div>
								</div>
							)}
						</div>
						<Link 
							href="/data-sources"
							className="p-2 rounded-lg hover:bg-purple-900/30 transition-colors duration-200 text-zinc-400 hover:text-zinc-200"
							title="Manage Data Sources"
						>
							<Database size={18} />
						</Link>
					</div>
				</div>
			</div>
		</header>
	);
} 