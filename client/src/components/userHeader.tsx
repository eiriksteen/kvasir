'use client';

import Image from 'next/image';
import Link from 'next/link';
import { Database, Bot, ChevronDown } from 'lucide-react';
import { useSession } from "next-auth/react";
import { useProject } from '@/hooks';
import { redirect } from 'next/navigation';
import { useState, useRef, useEffect } from 'react';
import { Project } from '@/types/project';

export default function UserHeader() {
	const { data: session } = useSession();
	const { selectedProject, projects, setSelectedProject } = useProject();
	const [showProjectDropdown, setShowProjectDropdown] = useState(false);
	const dropdownRef = useRef<HTMLDivElement>(null);

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
		setSelectedProject(project);
		setShowProjectDropdown(false);
	};

	const handleBackToMenu = () => {
		setSelectedProject(null);
		setShowProjectDropdown(false);
	};

	return (
		<header className="fixed top-0 left-0 right-0 z-50 bg-black">
			<div className="mx-auto px-4 sm:px-6 lg:pr-3">
				<div className="flex items-center justify-between h-12">
					{/* Logo and project button on the left */}
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
						
						{selectedProject && (
							<div className="relative" ref={dropdownRef}>
								<button
									onClick={() => setShowProjectDropdown(!showProjectDropdown)}
									className="text-zinc-400 hover:text-zinc-200 transition-colors px-3 py-1 rounded-md border border-zinc-700 hover:border-zinc-600 flex items-center space-x-1"
									title="Select Project"
								>
									<span className="text-sm font-medium">
										{selectedProject.name}
									</span>
									<ChevronDown size={14} className={`transition-transform ${showProjectDropdown ? 'rotate-180' : ''}`} />
								</button>
								
								{/* Project Dropdown */}
								{showProjectDropdown && (
									<div className="absolute top-full left-0 mt-1 w-64 bg-zinc-900 border border-zinc-800 rounded-lg shadow-lg z-50">
										<div className="p-2">
											{/* Back to Menu Button */}
											<button
												onClick={handleBackToMenu}
												className="w-full text-left px-3 py-2 text-sm text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded-md transition-colors"
											>
												Back to Menu
											</button>
											
											{/* Divider */}
											<div className="border-t border-zinc-800 my-2"></div>
											
											{/* Projects List */}
											<div className="max-h-48 overflow-y-auto">
												{projects?.map((project) => (
													<button
														key={project.id}
														onClick={() => handleProjectSelect(project)}
														className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors ${
															project.id === selectedProject?.id
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
										</div>
									</div>
								)}
							</div>
						)}
					</div>
					
					{/* Two buttons on the right */}
					<div className="flex items-center gap-2">
						<Link 
							href="/integration"
							className="p-2 rounded-lg hover:bg-purple-900/30 transition-colors duration-200 text-zinc-400 hover:text-zinc-200"
							title="Manage Datasets"
						>
							<Database size={18} />
						</Link>
						<Link 
							href="/model-integration"
							className="p-2 rounded-lg hover:bg-purple-900/30 transition-colors duration-200 text-zinc-400 hover:text-zinc-200"
							title="Model Integration"
						>
							<Bot size={18} />
						</Link>
					</div>
				</div>
			</div>
		</header>
	);
} 