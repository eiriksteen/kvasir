'use client';
import React from 'react';

import { useState, useMemo } from 'react';
import { Database, Plus, ChevronLeft, ChevronRight, BarChart3, Zap, TrendingUp } from 'lucide-react';
import { TimeSeriesDataset } from '@/types/datasets';
import { Automation } from '@/types/automations';
import { useAgentContext, useDatasets, useAnalysis, useProject } from '@/hooks';
import { useSession } from 'next-auth/react';
import { redirect } from 'next/navigation';
import { AnalysisJobResultMetadata } from '@/types/analysis';
import AddDatasetToProject from '@/components/data-integration/AddDatasetToProject';
import AddAnalysis from '@/components/analysis/AddAnalysis';

type ItemType = 'dataset' | 'analysis' | 'automation';

interface ListItemProps {
    item: TimeSeriesDataset | AnalysisJobResultMetadata | Automation;
    type: ItemType;
    isInContext: boolean;
    onClick: () => void;
}

function ListItem({ item, type, isInContext, onClick }: ListItemProps) {
    const getTheme = (type: ItemType) => {
        switch (type) {
            case 'dataset':
                return {
                    bg: isInContext ? 'bg-blue-500/10' : 'hover:bg-blue-500/5',
                    icon: <TrendingUp size={11} />,
                    iconColor: 'text-blue-400',
                    textColor: 'text-gray-200',
                    hover: 'hover:bg-blue-500/8'
                };
            case 'analysis':
                return {
                    bg: isInContext ? 'bg-purple-500/10' : 'hover:bg-purple-500/5',
                    icon: <BarChart3 size={11} />,
                    iconColor: 'text-purple-400',
                    textColor: 'text-gray-200',
                    hover: 'hover:bg-purple-500/8'
                };
            case 'automation':
                return {
                    bg: isInContext ? 'bg-orange-500/10' : 'hover:bg-orange-500/5',
                    icon: <Zap size={11} />,
                    iconColor: 'text-orange-400',
                    textColor: 'text-gray-200',
                    hover: 'hover:bg-orange-500/8'
                };
        }
    };

    const theme = getTheme(type);
    const name = 'name' in item ? item.name : `Analysis ${(item as AnalysisJobResultMetadata).jobId.slice(0, 6)}`;

    return (
        <div
            onClick={onClick}
            className={`group relative flex items-center gap-2 px-3 py-1.5 text-sm cursor-pointer transition-all duration-150 ${theme.bg} ${theme.hover}`}
        >
            <div className={`flex-shrink-0 ${theme.iconColor}`}>
                {theme.icon}
            </div>
            <span className={`truncate ${theme.textColor} font-mono text-xs`}>{name}</span>
        </div>
    );
}

// Component for merged concept + plus icons
function NewItemIcon({ type, size = 13 }: { type: ItemType; size?: number }) {
    const badgeClass = "absolute top-[-8px] right-[-8px] rounded-full p-0.5 z-10";
    const getIcon = () => {
        switch (type) {
            case 'dataset':
                return (
                    <div className="relative overflow-visible">
                        <Database size={size} />
                        <div className={badgeClass + " bg-blue-500 border border-blue-400/30"}>
                            <Plus size={size * 0.35} className="text-white" />
                        </div>
                    </div>
                );
            case 'analysis':
                return (
                    <div className="relative overflow-visible">
                        <BarChart3 size={size} />
                        <div className={badgeClass + " bg-purple-500 border border-purple-400/30"}>
                            <Plus size={size * 0.35} className="text-white" />
                        </div>
                    </div>
                );
            case 'automation':
                return (
                    <div className="relative overflow-visible">
                        <Zap size={size} />
                        <div className={badgeClass + " bg-orange-500 border border-orange-400/30"}>
                            <Plus size={size * 0.35} className="text-white" />
                        </div>
                    </div>
                );
        }
    };

    return getIcon();
}

interface SectionHeaderProps {
    title: string;
    count: number;
    color: 'blue' | 'purple' | 'orange';
    onToggle: () => void;
    onAdd: () => void;
}

function SectionHeader({ title, count, color, onToggle, onAdd }: SectionHeaderProps) {
    const getColorClasses = (color: 'blue' | 'purple' | 'orange') => {
        switch (color) {
            case 'blue':
                return {
                    bg: 'bg-blue-500/20',
                    border: 'border-blue-400/50',
                    text: 'text-blue-300',
                    icon: 'text-blue-300',
                    hover: 'hover:bg-blue-500/30',
                    buttonHover: 'hover:bg-blue-500/40',
                    buttonBg: 'bg-blue-500/15',
                };
            case 'purple':
                return {
                    bg: 'bg-purple-500/20',
                    border: 'border-purple-400/50',
                    text: 'text-purple-300',
                    icon: 'text-purple-300',
                    hover: 'hover:bg-purple-500/30',
                    buttonHover: 'hover:bg-purple-500/40',
                    buttonBg: 'bg-purple-500/15',
                };
            case 'orange':
                return {
                    bg: 'bg-orange-500/20',
                    border: 'border-orange-400/50',
                    text: 'text-orange-300',
                    icon: 'text-orange-300',
                    hover: 'hover:bg-orange-500/30',
                    buttonHover: 'hover:bg-orange-500/40',
                    buttonBg: 'bg-orange-500/15',
                };
        }
    };

    const colors = getColorClasses(color);
    const itemTypeMap: Record<string, ItemType> = {
        'Datasets': 'dataset',
        'Analysis': 'analysis',
        'Automations': 'automation'
    };
    const itemType = itemTypeMap[title];

    return (
        <div 
            className={`flex items-center justify-between px-3 py-2 cursor-pointer transition-colors ${colors.hover}`}
            onClick={onToggle}
        >
            <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-gray-400 bg-gray-800/50 px-1.5 py-0.5 rounded">
                    {count}
                </span>
                <span className={`text-xs font-semibold uppercase tracking-wider ${colors.text}`}>
                    {title}
                </span>
            </div>
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    onAdd();
                }}
                className={`p-1.5 rounded-md inline-flex items-center justify-center min-w-[32px] min-h-[32px] ${colors.buttonBg} border ${colors.border} transition-all duration-200 ${colors.buttonHover} hover:scale-105`}
                title={`Add ${title.slice(0, -1)}`}
            >
                <div className={colors.icon}>
                    <NewItemIcon type={itemType} />
                </div>
            </button>
        </div>
    );
}

interface OntologyBarProps {
    projectId: string;
}

export default function OntologyBar({ projectId }: OntologyBarProps) {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [showAddDatasetToProject, setShowAddDatasetToProject] = useState(false);
    const [showAddAnalysis, setShowAddAnalysis] = useState(false);
    const [expandedSections, setExpandedSections] = useState({
        datasets: false,
        analysis: false,
        automations: false
    });
    const { data: session } = useSession();
    const { selectedProject } = useProject(projectId);
    const { 
        datasetsInContext, 
        addDatasetToContext, 
        removeDatasetFromContext,
        analysisesInContext,
        addAnalysisToContext,
        removeAnalysisFromContext
    } = useAgentContext();

    if (!session) {
        redirect("/login");
    }

    const { datasets } = useDatasets();
    const automations: Automation[] = [];
    const { analysisJobResults } = useAnalysis();

    const filteredAnalysis = useMemo(() => {
        if (!selectedProject || !analysisJobResults?.analysesJobResults) return [];
        return analysisJobResults.analysesJobResults
            .filter(analysis => selectedProject.analysisIds.includes(analysis.jobId))
            .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
    }, [selectedProject, analysisJobResults]);

    const filteredAutomations = useMemo(() => {
        if (!selectedProject || !automations) return [];
        return automations.filter(automation => 
            selectedProject.automationIds.includes(automation.id)
        );
    }, [selectedProject, automations]);

    const toggleSection = (section: keyof typeof expandedSections) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    const handleDatasetToggle = (dataset: TimeSeriesDataset) => {
        const isActive = datasetsInContext.timeSeries.some((d: TimeSeriesDataset) => d.id === dataset.id);
        if (isActive) {
            removeDatasetFromContext(dataset);
        } else {
            addDatasetToContext(dataset);
        }
    };

    const isDatasetInContext = (datasetId: string) => 
        datasetsInContext.timeSeries.some((dataset: TimeSeriesDataset) => dataset.id === datasetId);

    const handleAnalysisToggle = (analysis: AnalysisJobResultMetadata) => {
        const isActive = analysisesInContext.some((a: AnalysisJobResultMetadata) => a.jobId === analysis.jobId);
        if (isActive) {
            removeAnalysisFromContext(analysis);
        } else {
            addAnalysisToContext(analysis);
        }
    };

    const renderContent = () => {
        if (!selectedProject) {
            return (
                <div className="flex flex-col h-full items-center justify-center p-4">
                    <p className="text-sm text-gray-400 mb-2">No project selected</p>
                    <p className="text-xs text-gray-500 text-center">Use the exit button in the header to return to project selection</p>
                </div>
            );
        }

        return (
            <div className="flex flex-col h-full">
                {/* Header */}
                <div className="flex items-center justify-between px-3 py-2 border-b border-gray-800 bg-gray-900/50">
                    <div className="flex flex-col">
                        <h2 className="text-xs font-mono uppercase tracking-wider text-gray-400 mb-0.5">
                            Ontology
                        </h2>
                    </div>
                    <button
                        onClick={() => setIsCollapsed(!isCollapsed)}
                        className="p-1 rounded text-gray-400 hover:text-white hover:bg-gray-700 transition-colors"
                        title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                    >
                        {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto">
                    {/* Datasets Section */}
                    <div className="border-b border-gray-800">
                        <SectionHeader
                            title="Datasets"
                            count={datasets?.timeSeries.filter(dataset => selectedProject.datasetIds.includes(dataset.id)).length || 0}
                            color="blue"
                            onToggle={() => toggleSection('datasets')}
                            onAdd={() => setShowAddDatasetToProject(true)}
                        />
                        {expandedSections.datasets && (
                            <div className="bg-blue-500/5 border-l-2 border-blue-500/20">
                                {datasets?.timeSeries
                                    .filter(dataset => selectedProject.datasetIds.includes(dataset.id))
                                    .map((dataset) => (
                                        <ListItem 
                                            key={dataset.id}
                                            item={dataset}
                                            type="dataset"
                                            isInContext={isDatasetInContext(dataset.id)}
                                            onClick={() => handleDatasetToggle(dataset)}
                                        />
                                    ))}
                                {datasets?.timeSeries.filter(dataset => selectedProject.datasetIds.includes(dataset.id)).length === 0 && (
                                    <div className="px-3 py-4 text-center">
                                        <Database size={16} className="text-blue-400/40 mx-auto mb-2" />
                                        <p className="text-xs text-gray-500">No datasets</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Analysis Section */}
                    <div className="border-b border-gray-800">
                        <SectionHeader
                            title="Analysis"
                            count={filteredAnalysis.length}
                            color="purple"
                            onToggle={() => toggleSection('analysis')}
                            onAdd={() => setShowAddAnalysis(true)}
                        />
                        {expandedSections.analysis && (
                            <div className="bg-purple-500/5 border-l-2 border-purple-500/20">
                                {filteredAnalysis.map((analysis) => (
                                    <ListItem
                                        key={analysis.jobId}
                                        item={analysis}
                                        type="analysis"
                                        isInContext={analysisesInContext.some((a: AnalysisJobResultMetadata) => a.jobId === analysis.jobId)}
                                        onClick={() => handleAnalysisToggle(analysis)}
                                    />
                                ))}
                                {filteredAnalysis.length === 0 && (
                                    <div className="px-3 py-4 text-center">
                                        <BarChart3 size={16} className="text-purple-400/40 mx-auto mb-2" />
                                        <p className="text-xs text-gray-500">No analysis</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Automations Section */}
                    <div className="border-b border-gray-800">
                        <SectionHeader
                            title="Automations"
                            count={filteredAutomations.length}
                            color="orange"
                            onToggle={() => toggleSection('automations')}
                            onAdd={() => {
                                {/* TODO: Implement add automation */};
                            }}
                        />
                        {expandedSections.automations && (
                            <div className="bg-orange-500/5 border-l-2 border-orange-500/20">
                                {filteredAutomations.map((automation) => (
                                    <ListItem
                                        key={automation.id}
                                        item={automation}
                                        type="automation"
                                        isInContext={false}
                                        onClick={() => {}}
                                    />
                                ))}
                                {filteredAutomations.length === 0 && (
                                    <div className="px-3 py-4 text-center">
                                        <Zap size={16} className="text-orange-400/40 mx-auto mb-2" />
                                        <p className="text-xs text-gray-500">No automations</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="mt-12">
            <div className={`flex flex-col h-full bg-gray-950 border-r border-gray-800 text-white transition-all duration-300 ${isCollapsed ? 'w-10' : 'w-[260px]'}`}>
                {!isCollapsed && renderContent()}

                {isCollapsed && (
                    <div className="flex flex-col h-full">
                        {/* Header for collapsed state */}
                        <div className="flex items-center justify-center p-2 border-b border-gray-800 bg-gray-900/50">
                            <button
                                onClick={() => setIsCollapsed(!isCollapsed)}
                                className="p-1 rounded text-gray-400 hover:text-white hover:bg-gray-700 transition-colors"
                                title="Expand sidebar"
                            >
                                <ChevronRight size={14} />
                            </button>
                        </div>
                        
                        {/* Collapsed content */}
                        <div className="flex flex-col items-center pt-3 gap-2">
                            <button
                                onClick={() => setShowAddDatasetToProject(true)}
                                className="p-2 rounded-md text-blue-400 hover:text-blue-300 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 hover:border-blue-500/40 transition-all duration-200 hover:scale-105"
                                title="Add Dataset to Project"
                            >
                                <NewItemIcon type="dataset" size={14} />
                            </button>
                            <button
                                onClick={() => setShowAddAnalysis(true)}
                                className="p-2 rounded-md text-purple-400 hover:text-purple-300 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/20 hover:border-purple-500/40 transition-all duration-200 hover:scale-105"
                                title="Add Analysis"
                            >
                                <NewItemIcon type="analysis" size={14} />
                            </button>
                            <button
                                onClick={() => {
                                    {/* TODO: Implement add automation */};
                                }}
                                className="p-2 rounded-md text-orange-400 hover:text-orange-300 bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/20 hover:border-orange-500/40 transition-all duration-200 hover:scale-105"
                                title="Add Automation"
                            >
                                <NewItemIcon type="automation" size={14} />
                            </button>
                        </div>
                    </div>
                )}
            </div>

            <AddDatasetToProject
                isOpen={showAddDatasetToProject}
                onClose={() => setShowAddDatasetToProject(false)}
                projectId={projectId}
            />

            <AddAnalysis
                isOpen={showAddAnalysis}
                onClose={() => setShowAddAnalysis(false)}
                projectId={projectId}
            />
        </div>
    );
}
