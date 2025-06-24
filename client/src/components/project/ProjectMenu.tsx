'use client';

import React, { useState } from 'react';
import { AlertTriangle, Loader2, ChevronRight, FolderGit2, X, Plus } from 'lucide-react';
import { useProjects } from '@/hooks/useProject';
import { Project } from '@/types/project';
import Image from 'next/image';
import { useRouter } from 'next/navigation';

export default function ProjectMenu() {
  const { projects, isLoading, triggerCreateNewProject } = useProjects();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showOpenModal, setShowOpenModal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name.trim()) {
      setError('Please provide a project name');
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      const newProject = await triggerCreateNewProject({ name, description });
      router.push(`/projects/${newProject.id}`);
      setShowCreateModal(false);
      setName('');
      setDescription('');
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleProjectSelect = (project: Project) => {
    router.push(`/projects/${project.id}`);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center flex-1">
        <div className="text-center">
          <Loader2 className="w-6 h-6 animate-spin text-zinc-400 mx-auto mb-3" />
          <p className="text-zinc-400 text-sm">Loading projects...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl p-6">
      <div className="max-w-lg mx-auto">
        {/* Header with Logo */}
        <div className="mb-12">
          <Image
            src="/miyawtext.png"
            alt="Miya Logo"
            width={160}
            height={160}
            priority
          />
        </div>

        {/* Main Action Buttons */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Open Project Button */}
          <button
            onClick={() => setShowOpenModal(true)}
            className="group p-6 bg-zinc-900/50 border border-zinc-800 rounded-lg hover:bg-zinc-900/80 hover:border-zinc-700 transition-all duration-200"
          >
            <div className="flex flex-col items-center text-center space-y-3">
              <div className="p-3 bg-zinc-800/50 rounded-lg border border-zinc-700/30">
                <FolderGit2 size={20} className="text-zinc-400" />
              </div>
              <div>
                <h3 className="text-base font-medium text-zinc-100">Open project</h3>
              </div>
            </div>
          </button>

          {/* Create Project Button */}
          <button
            onClick={() => setShowCreateModal(true)}
            className="group p-6 bg-zinc-900/50 border border-zinc-800 rounded-lg hover:bg-zinc-900/80 hover:border-zinc-700 transition-all duration-200"
          >
            <div className="flex flex-col items-center text-center space-y-3">
              <div className="p-3 bg-zinc-800/50 rounded-lg border border-zinc-700/30">
                <Plus size={20} className="text-zinc-400" />
              </div>
              <div>
                <h3 className="text-base font-medium text-zinc-100">Create project</h3>
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Open Project Modal */}
      {showOpenModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
              <h2 className="text-lg font-semibold text-zinc-100">Open Project</h2>
              <button
                onClick={() => setShowOpenModal(false)}
                className="p-2 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded-md transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {projects && projects.length > 0 ? (
                <div className="space-y-3">
                  {projects.slice().reverse().map((project) => (
                    <button
                      key={project.id}
                      onClick={() => handleProjectSelect(project)}
                      className="w-full p-4 text-left bg-zinc-800/30 border border-zinc-700/30 rounded-lg hover:bg-zinc-800/50 hover:border-zinc-700/50 transition-all duration-200 group"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="p-2 bg-zinc-700/50 rounded-lg">
                            <FolderGit2 size={16} className="text-zinc-400" />
                          </div>
                          <div className="text-left">
                            <h3 className="text-sm font-medium text-zinc-200">{project.name}</h3>
                            {project.description && (
                              <p className="text-xs text-zinc-400 mt-1 line-clamp-1">{project.description}</p>
                            )}
                          </div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-zinc-500 group-hover:text-zinc-300 transition-colors" />
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="p-4 bg-zinc-800/30 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                    <FolderGit2 size={20} className="text-zinc-400" />
                  </div>
                  <h3 className="text-base font-medium text-zinc-200 mb-2">No projects found</h3>
                  <p className="text-sm text-zinc-400">Create your first project to get started</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
              <h2 className="text-lg font-semibold text-zinc-100">Create New Project</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded-md transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            <div className="p-6">
              <form onSubmit={handleCreateProject} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-2 uppercase tracking-wide">
                    Project Name
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter project name"
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 text-sm placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-600 focus:border-zinc-600 transition-colors"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-2 uppercase tracking-wide">
                    Description
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Optional project description"
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 text-sm placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-600 focus:border-zinc-600 transition-colors resize-none"
                    rows={3}
                  />
                </div>

                {error && (
                  <div className="p-3 bg-red-900/20 border border-red-800/30 rounded-lg text-xs text-red-300 flex items-center">
                    <AlertTriangle size={12} className="mr-2 flex-shrink-0"/>
                    {error}
                  </div>
                )}

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 text-sm text-zinc-400 hover:text-zinc-200 transition-colors font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting || !name.trim()}
                    className="px-6 py-2 bg-zinc-700 hover:bg-zinc-600 text-white text-sm rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 size={14} className="animate-spin mr-2" /> Creating...
                      </>
                    ) : (
                      'Create Project'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 