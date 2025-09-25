'use client';

import Image from 'next/image';
import Link from 'next/link';
import { Database, ChevronDown } from 'lucide-react';
import { useProjects, useProject } from '@/hooks';
import { useRouter } from 'next/navigation';
import { useState, useRef, useEffect } from 'react';
import { Project } from '@/types/project';
import { UUID } from 'crypto';

interface UserHeaderProps {
	projectId: UUID;
} 

export default function UserHeader({ projectId }: UserHeaderProps) {
	const { projects } = useProjects();
	const { project } = useProject(projectId);
	const [showProjectDropdown, setShowProjectDropdown] = useState(false);
	const dropdownRef = useRef<HTMLDivElement>(null);
	const router = useRouter();

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
		<header className="fixed top-0 left-0 right-0 z-50 bg-white">
			<div className="mx-auto px-4 sm:px-6 lg:pr-3">
				<div className="flex items-center justify-between h-12">
					{/* Logo and Project Title on the left */}
					<div className="flex items-center space-x-4">
						<Link href="/projects">
							<div className="relative w-[20px] h-[20px]">
								<Image
									src="/kvasir-logo.png"
									alt="Kvasir logo"
									fill
									priority
									className="object-contain"
								/>
							</div>
						</Link>
						
						{/* Project Title with Slash */}
						{project && (
							<div className="flex items-center space-x-3">
								<div className="text-gray-800 text-lg font-light">/</div>
								<div className="flex flex-col">
									<div className="text-gray-800 text-sm font-medium">
										{project.name}
									</div>
									{/* {project.description && (
										<div className="text-gray-800 text-xs truncate max-w-[200px]">
											{project.description}
										</div>
									)} */}
								</div>
							</div>
						)}
					</div>
					
					{/* Three buttons on the right */}
					<div className="flex items-center gap-2">
						<div className="relative" ref={dropdownRef}>
							<button
								onClick={() => setShowProjectDropdown(!showProjectDropdown)}
								className="text-gray-800 hover:text-gray-200 transition-colors px-3 py-1 rounded-md border border-[#000034] flex items-center space-x-1"
								title="Select Project"
							>
								<span className="text-sm font-medium">
									Projects
								</span>
								<ChevronDown size={14} className={`transition-transform ${showProjectDropdown ? 'rotate-180' : ''}`} />
							</button>
							
							{/* Project Dropdown */}
							{showProjectDropdown && (
								<div className="absolute top-full right-0 mt-1 w-64 bg-white border border-gray-300 rounded-lg shadow-lg z-50">
									<div className="p-2">
										{/* Projects List */}
										<div className="max-h-48 overflow-y-auto">
											{projects?.slice().reverse().map((project) => (
												<button
													key={project.id}
													onClick={() => handleProjectSelect(project)}
													className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors ${
														project.id === projectId
															? 'bg-blue-50 text-gray-900'
															: 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
													}`}
												>
													<div className="font-medium">{project.name}</div>
													{project.description && (
														<div className="text-xs text-gray-500 mt-1 truncate">
															{project.description}
														</div>
													)}
												</button>
											))}
										</div>

										{/* Divider */}
										<div className="border-t border-gray-300 mt-1 mb-1"></div>

										{/* Back to Menu Button */}
										<button
											onClick={handleBackToMenu}
											className="w-full text-left px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors font-medium"
										>
											← Back to Menu
										</button>
									</div>
								</div>
							)}
						</div>
						<Link 
							href="/data-sources"
							className="p-2 rounded-lg hover:bg-[#000034] transition-colors duration-200 text-[#000034] hover:text-gray-200"
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