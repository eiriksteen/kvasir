'use client';

import React, { useState } from 'react';
import { Plus, AlertTriangle, Loader2, ChevronRight } from 'lucide-react';
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
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-[#050a14] border border-[#101827] rounded-lg w-full max-w-md mx-4 p-6">
          <div className="flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-[#050a14] border border-[#101827] rounded-lg w-full max-w-md mx-4">
        <div className="flex items-center justify-between p-4 border-b border-[#101827]">
          <h3 className="text-md font-semibold text-zinc-200">Select Project</h3>
          <button
            onClick={() => onSelect(projects?.[0] || null)}
            className="text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            ×
          </button>
        </div>

        <div className="flex flex-col max-h-[80vh]">
          {/* Projects List */}
          <div className="flex-1 overflow-y-auto min-h-0">
            {projects && projects.length > 0 ? (
              <div className="space-y-1 p-2">
                {projects.map((project) => (
                  <button
                    key={project.id}
                    onClick={() => handleProjectSelect(project)}
                    className="w-full p-3 text-left bg-[#0a101c] border border-[#101827] rounded-lg hover:bg-[#0f1729] transition-colors group"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-zinc-200">{project.name}</h3>
                        {project.description && (
                          <p className="text-sm text-zinc-400 mt-0.5 line-clamp-1">{project.description}</p>
                        )}
                      </div>
                      <ChevronRight className="w-5 h-5 text-zinc-500 group-hover:text-zinc-300 transition-colors" />
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-48 text-zinc-500">
                <p className="text-sm">No projects yet</p>
                <p className="text-xs mt-1">Create your first project below</p>
              </div>
            )}
          </div>

          {/* Create Project Section */}
          <div className="border-t border-[#101827] p-4">
            {isCreating ? (
              <div className="bg-[#050a14] border border-[#101827] rounded-lg">
                <div className="flex items-center justify-between p-4 border-b border-[#101827]">
                  <h3 className="text-md font-semibold text-zinc-200">Create New Project</h3>
                  <button
                    onClick={() => setIsCreating(false)}
                    className="text-zinc-400 hover:text-zinc-200 transition-colors"
                  >
                    ×
                  </button>
                </div>

                <form onSubmit={handleCreateProject} className="p-4 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                      Project Name *
                    </label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Enter project name..."
                      className="w-full px-3 py-2 bg-[#0a101c] border border-zinc-700 rounded-md text-zinc-200 text-sm placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                      Description (Optional)
                    </label>
                    <textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Describe the purpose and scope of this project..."
                      className="w-full px-3 py-2 bg-[#0a101c] border border-zinc-700 rounded-md text-zinc-200 text-sm placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600"
                      rows={3}
                    />
                  </div>

                  {error && (
                    <div className="p-3 bg-red-900/30 border border-red-700/50 rounded-md text-sm text-red-300 flex items-center">
                      <AlertTriangle size={16} className="mr-2 flex-shrink-0"/>
                      {error}
                    </div>
                  )}

                  <div className="flex justify-end gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setIsCreating(false)}
                      className="px-4 py-2 text-zinc-300 hover:text-zinc-100 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmitting || !name.trim()}
                      className="px-5 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-md hover:from-blue-500 hover:to-blue-600 transition-all shadow-md hover:shadow-lg border border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none disabled:from-zinc-600 disabled:to-zinc-700 disabled:border-zinc-500 flex items-center"
                    >
                      {isSubmitting ? (
                        <>
                          <Loader2 size={16} className="animate-spin mr-2" /> Creating...
                        </>
                      ) : (
                        <>
                          <Plus size={16} className="mr-1.5" /> Create Project
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>
            ) : (
              <button
                onClick={() => setIsCreating(true)}
                className="w-full px-4 py-2.5 bg-[#0a101c] border border-[#101827] rounded-lg text-zinc-300 hover:bg-[#0f1729] transition-colors flex items-center justify-center gap-2"
              >
                <Plus size={16} />
                <span>Create New Project</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
