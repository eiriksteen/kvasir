'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { Plus, AlertTriangle, Loader2, ChevronRight, FolderGit2 } from 'lucide-react';
import { useProject } from '@/hooks/useProject';
import { Project } from '@/types/project';

interface SelectProjectProps {
  onSelect: (project: Project) => void;
}

export default function SelectProject({ onSelect }: SelectProjectProps) {
  const { projects, isLoading, createNewProject, setSelectedProject } = useProject();
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name.trim()) {
      setError('Please provide a project name');
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const newProject = await createNewProject({ name, description });
      setSelectedProject(newProject);
      onSelect(newProject);
      setIsCreating(false);
      setName('');
      setDescription('');
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleProjectSelect = (project: Project) => {
    setSelectedProject(project);
    onSelect(project);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zinc-950">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-zinc-400">Loading projects...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-3/5 bg-zinc-950 flex items-center justify-center p-8 ">
      <div className="w-full max-w-4xl mx-auto">
        {/* Header with Logo and Tagline */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-6">
            <Image
              src="/miyawtext.png"
              alt="Miya"
              width={300}
              height={63}
              priority
              className="h-auto"
            />
          </div>
          <p className="text-xl text-zinc-300 font-light">
            Make data analysis and AI seamless
          </p>
        </div>

        {/* Main Content */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-zinc-800/50 border-b border-zinc-700 px-6 py-4">
            <h2 className="text-lg font-semibold text-zinc-100">
              {isCreating ? 'Create New Project' : 'Select a Project'}
            </h2>
            {!isCreating && (
              <p className="text-sm text-zinc-400 mt-1">
                Choose a project to get started or create a new one
              </p>
            )}
          </div>

          <div className="p-6">
            {isCreating ? (
              // Create Project Form
              <form onSubmit={handleCreateProject} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Project Name *
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter project name..."
                    className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 text-base placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Description (Optional)
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Describe the purpose and scope of this project..."
                    className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 text-base placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none"
                    rows={4}
                  />
                </div>

                {error && (
                  <div className="p-4 bg-red-900/20 border border-red-700/50 rounded-lg text-sm text-red-300 flex items-center">
                    <AlertTriangle size={16} className="mr-2 flex-shrink-0"/>
                    {error}
                  </div>
                )}

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setIsCreating(false)}
                    className="px-6 py-2.5 text-zinc-300 hover:text-zinc-100 transition-colors font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting || !name.trim()}
                    className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-500 hover:to-blue-600 transition-all shadow-lg hover:shadow-xl border border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none disabled:from-zinc-600 disabled:to-zinc-700 disabled:border-zinc-500 flex items-center font-medium"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 size={16} className="animate-spin mr-2" /> Creating...
                      </>
                    ) : (
                      <>
                        <Plus size={16} className="mr-2" /> Create Project
                      </>
                    )}
                  </button>
                </div>
              </form>
            ) : (
              // Project Selection
              <div className="space-y-4">
                {projects && projects.length > 0 ? (
                  <div className="grid gap-3">
                    {projects.map((project) => (
                      <button
                        key={project.id}
                        onClick={() => handleProjectSelect(project)}
                        className="w-full p-4 text-left bg-zinc-800 border border-zinc-700 rounded-lg hover:bg-zinc-700/50 hover:border-zinc-600 transition-all duration-200 group"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <div className="p-2 bg-zinc-700 rounded-lg">
                              <FolderGit2 size={20} className="text-zinc-400" />
                            </div>
                            <div className="text-left">
                              <h3 className="text-base font-medium text-zinc-200">{project.name}</h3>
                              {project.description && (
                                <p className="text-sm text-zinc-400 mt-0.5 line-clamp-1">{project.description}</p>
                              )}
                            </div>
                          </div>
                          <ChevronRight className="w-5 h-5 text-zinc-500 group-hover:text-zinc-300 transition-colors" />
                        </div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="p-4 bg-zinc-800 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                      <FolderGit2 size={24} className="text-zinc-400" />
                    </div>
                    <h3 className="text-lg font-medium text-zinc-200 mb-2">No projects yet</h3>
                    <p className="text-zinc-400 mb-6">Create your first project to get started</p>
                  </div>
                )}

                {/* Create New Project Button */}
                <div className="pt-4 border-t border-zinc-700">
                  <button
                    onClick={() => setIsCreating(true)}
                    className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-300 hover:bg-zinc-700/50 hover:border-zinc-600 transition-all duration-200 flex items-center justify-center gap-2 font-medium"
                  >
                    <Plus size={18} />
                    <span>Create New Project</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
