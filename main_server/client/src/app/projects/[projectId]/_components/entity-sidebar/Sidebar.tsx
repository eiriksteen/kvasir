'use client';

import React, { useEffect } from 'react';
import { useState } from 'react';
import { Code, Hammer } from 'lucide-react';
import { useProject } from '@/hooks';
import { useSession } from 'next-auth/react';
import { redirect } from 'next/navigation';
import { UUID } from 'crypto';
import CodebaseTree from '@/app/projects/[projectId]/_components/entity-sidebar/CodebaseTree';
import EntityTree from '@/app/projects/[projectId]/_components/entity-sidebar/EntityTree';
import AddEntityButton from '@/app/projects/[projectId]/_components/entity-sidebar/AddEntityButton';


interface EntitySidebarProps {
    projectId: UUID;
    openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void;
}

export default function EntitySidebar({ projectId, openTab }: EntitySidebarProps) {
    const [width, setWidth] = useState(260);
    const [isDragging, setIsDragging] = useState(false);
    
    const DEFAULT_WIDTH = 260;
    const MIN_WIDTH = 160;
    const COLLAPSE_THRESHOLD = 100;
    const COLLAPSED_WIDTH = 40;
    const [viewMode, setViewMode] = useState<'code' | 'entities'>('entities');
    const { data: session } = useSession();
    const { project } = useProject(projectId);

    if (!session) {
        redirect("/login");
    }

    const MAX_WIDTH = typeof window !== 'undefined' ? window.innerWidth * 0.3 : 400;

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!isDragging) return;
            e.preventDefault();
            
            let newWidth = e.clientX;
            
            // Auto-collapse immediately when dragged below threshold
            if (newWidth < COLLAPSE_THRESHOLD) {
                newWidth = COLLAPSED_WIDTH;
            } else {
                newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, newWidth));
            }
            
            setWidth(newWidth);
        };

        const handleMouseUp = () => {
            setIsDragging(false);
        };

        if (isDragging) {
            document.addEventListener("mousemove", handleMouseMove);
            document.addEventListener("mouseup", handleMouseUp);
        }

        return () => {
            document.removeEventListener("mousemove", handleMouseMove);
            document.removeEventListener("mouseup", handleMouseUp);
        };
    }, [isDragging, MIN_WIDTH, MAX_WIDTH, COLLAPSE_THRESHOLD, COLLAPSED_WIDTH]);

    const handleStartDrag = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleExpandSidebar = () => {
        setWidth(DEFAULT_WIDTH);
    };

    const isCollapsed = width <= COLLAPSED_WIDTH;

    // Keyboard shortcut for CMD + B to toggle sidebar
    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if ((event.metaKey || event.ctrlKey) && event.key === 'b') {
                event.preventDefault();
                if (isCollapsed) {
                    handleExpandSidebar();
                } else {
                    setWidth(COLLAPSED_WIDTH);
                }
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [isCollapsed]);

    const renderContent = () => {
        if (!project) {
            return (
                <div className="flex flex-col h-full items-center justify-center p-4">
                    <p className="text-sm text-gray-400 mb-2">No project selected</p>
                    <p className="text-xs text-gray-500 text-center">Use the exit button in the header to return to project selection</p>
                </div>
            );
        }

        return (
            <div className="flex flex-col h-full">
                {/* View Mode Switcher */}
                <div className="flex">
                    <button
                        onClick={() => setViewMode('entities')}
                        className={`flex-1 flex items-center justify-center h-7 transition-all ${
                            viewMode === 'entities'
                                ? 'bg-gray-200'
                                : 'bg-gray-100 hover:bg-gray-150'
                        }`}
                        style={{
                            boxShadow: viewMode === 'entities' ? 'inset 0 -2px 0 0 rgb(31 41 55)' : 'inset 0 -1px 0 0 rgb(156 163 175)'
                        }}
                    >
                        <Hammer size={14} className="text-gray-800" />
                    </button>
                    <button
                        onClick={() => setViewMode('code')}
                        className={`flex-1 flex items-center justify-center h-7 transition-all ${
                            viewMode === 'code'
                                ? 'bg-gray-200'
                                : 'bg-gray-100 hover:bg-gray-150'
                        }`}
                        style={{
                            boxShadow: viewMode === 'code' ? 'inset 0 -2px 0 0 rgb(31 41 55)' : 'inset 0 -1px 0 0 rgb(156 163 175)'
                        }}
                    >
                        <Code size={14} className="text-gray-800" />
                    </button>
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto">
                    {viewMode === 'code' ? (
                        <div className="h-full bg-gray-50">
                            <CodebaseTree 
                                projectId={projectId} 
                                onFileClick={(filePath) => openTab(filePath, true, undefined, filePath)}
                            />
                        </div>
                    ) : (
                        <EntityTree projectId={projectId} openTab={openTab} />
                    )}
                </div>
            </div>
        );
    };

    return (
        <div className="mt-12">
            <div 
                className="flex flex-col h-full bg-gray-100 border-r border-gray-200 text-gray-800 relative flex-shrink-0"
                style={{ width: `${width}px` }}
            >
                {/* Drag handle */}
                <div 
                    onMouseDown={handleStartDrag}
                    className="absolute top-0 bottom-0 right-0 w-2 cursor-col-resize z-10 hover:bg-gray-300 transition-colors"
                />

                {!isCollapsed && renderContent()}

                {isCollapsed && (
                    <div className="flex flex-col h-full">
                        {/* Data Source button at top */}
                        <div className="flex items-center justify-center h-7 border-b border-t border-gray-400 bg-gray-100">
                            <AddEntityButton type="data_source" size={11} projectId={projectId} />
                        </div>

                        {/* Centered entity buttons */}
                        <div className="flex-1 flex flex-col items-center justify-center gap-2">
                            <AddEntityButton type="dataset" size={11} projectId={projectId} />
                            <AddEntityButton type="model_entity" size={11} projectId={projectId} />
                            <AddEntityButton type="analysis" size={11} projectId={projectId} />
                            <AddEntityButton type="pipeline" size={11} projectId={projectId} />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}