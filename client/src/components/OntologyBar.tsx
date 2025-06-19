'use client';

import { useState, useMemo } from 'react';
import { Database, Plus, Check, ChevronLeft, ChevronRight, FolderGit2, BarChart3, Zap, ChevronDown, ChevronUp, Download } from 'lucide-react';
import { TimeSeriesDataset } from '@/types/datasets';
import { Automation } from '@/types/automations';
import { useAgentContext, useDatasets, useAnalysis, useProject } from '@/hooks';
import { useSession } from 'next-auth/react';
import { redirect } from 'next/navigation';
import { AnalysisJobResultMetadata } from '@/types/analysis';
import IntegrationManager from './integration/IntegrationManager';
import AddAnalysis from './AddAnalysis';

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
                    bg: isInContext ? 'bg-[#0a101c] border-[#2a4170]' : 'bg-[#050a14] border-[#101827]',
                    hover: 'hover:bg-[#0a101c]',
                    icon: <Database size={10} />,
                    iconColor: 'text-blue-300',
                    button: {
                        bg: isInContext 
                            ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white border-blue-500 shadow-blue-900/30'
                            : 'bg-gradient-to-r from-[#1a2438] to-[#273349] text-blue-300 hover:text-white hover:from-blue-600 hover:to-blue-700 border-[#2a4170]'
                    }
                };
            case 'analysis':
                return {
                    bg: isInContext ? 'bg-[#2a1c30] border-purple-800' : 'bg-[#1a1625]/80 border-[#271a30]',
                    hover: 'hover:bg-[#2a1c30]',
                    icon: <BarChart3 size={10} />,
                    iconColor: 'text-purple-300',
                    button: {
                        bg: isInContext 
                            ? 'bg-gradient-to-r from-purple-600 to-purple-700 text-white border-purple-500 shadow-purple-900/30'
                            : 'bg-gradient-to-r from-[#1a1625] to-[#271a30] text-purple-300 hover:text-white hover:from-purple-600 hover:to-purple-700 border-[#271a30]'
                    }
                };
            case 'automation':
                return {
                    bg: isInContext ? 'bg-[#2a1c30] border-purple-800' : 'bg-[#1a1625]/80 border-[#271a30]',
                    hover: 'hover:bg-[#2a1c30]',
                    icon: <Zap size={10} />,
                    iconColor: 'text-purple-300',
                    button: {
                        bg: isInContext 
                            ? 'bg-gradient-to-r from-purple-600 to-purple-700 text-white border-purple-500 shadow-purple-900/30'
                            : 'bg-gradient-to-r from-[#1a1625] to-[#271a30] text-purple-300 hover:text-white hover:from-purple-600 hover:to-purple-700 border-[#271a30]'
                    }
                };
        }
    };

    const theme = getTheme(type);
    const name = 'name' in item ? item.name : `Analysis ${(item as AnalysisJobResultMetadata).jobId.slice(0, 6)}`;

    return (
        <div
            onClick={onClick}
            className={`p-3 rounded-lg cursor-pointer transition-all duration-200 ${theme.hover} border-2 ${theme.bg}`}
        >
            <div className="flex justify-between items-center pr-2">
                <div className="flex-1">
                    <div className="text-sm font-medium">{name}</div>
                </div>
                
                <button 
                    onClick={(e) => {
                        e.stopPropagation();
                        onClick();
                    }}
                    className={`p-1.5 rounded-full border shadow-md ${theme.button.bg}`}
                    title={isInContext ? "Remove from context" : "Add to chat context"}
                >
                    {isInContext ? <Check size={14} /> : <ChevronRight size={14} />}
                </button>
            </div>
        </div>
    );
}

export default function OntologyBar() {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [showIntegrationManager, setShowIntegrationManager] = useState(false);
    const [showAddAnalysis, setShowAddAnalysis] = useState(false);
    const [expandedSections, setExpandedSections] = useState({
        datasets: true,
        analysis: true,
        automations: true
    });
    const { data: session } = useSession();
    const { selectedProject } = useProject();
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
                    <p className="text-sm text-zinc-400 mb-4">No project selected</p>
                    <p className="text-xs text-zinc-500 text-center">Use the exit button in the header to return to project selection</p>
                </div>
            );
        }

        return (
            <div className="flex flex-col h-full">
                <div className="w-full p-3 bg-[#111827] border-b border-[#1a2438] text-left">
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{selectedProject.name}</span>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto">
                    {/* Datasets Section */}
                    <div className="border-b border-[#1a2438]">
                        <div className="flex items-center justify-between p-1 hover:bg-[#1a2438] transition-colors rounded">
                            <button
                                onClick={() => toggleSection('datasets')}
                                className="flex items-center gap-2 p-2 rounded flex-1"
                            >
                                {expandedSections.datasets ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                <span className="text-sm font-medium">Datasets</span>
                            </button>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setShowIntegrationManager(true);
                                }}
                                className="px-3 py-1.5 rounded-md border shadow-md bg-gradient-to-r from-[#1a2438] to-[#273349] text-blue-300 hover:text-white hover:from-blue-600 hover:to-blue-700 border-[#2a4170] text-xs font-medium flex items-center gap-1.5"
                                title="Import Data"
                            >
                                <Download size={12} />
                                <span>Import Data</span>
                            </button>
                        </div>
                        {expandedSections.datasets && (
                            <div className="p-1 space-y-2">
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
                            </div>
                        )}
                    </div>

                    {/* Analysis Section */}
                    <div className="border-b border-[#1a2438]">
                        <div className="flex items-center justify-between p-1 hover:bg-[#1a2438] transition-colors rounded">
                            <button
                                onClick={() => toggleSection('analysis')}
                                className="flex items-center gap-2 p-2 rounded flex-1"
                            >
                                {expandedSections.analysis ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                <span className="text-sm font-medium">Analysis</span>
                            </button>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setShowAddAnalysis(true);
                                }}
                                className="px-3 py-1.5 rounded-md border shadow-md bg-gradient-to-r from-[#1a1625] to-[#271a30] text-purple-300 hover:text-white hover:from-purple-600 hover:to-purple-700 border-[#271a30] text-xs font-medium flex items-center gap-1.5"
                                title="Add Analysis"
                            >
                                <Plus size={14} />
                                <span>Add Analysis</span>
                            </button>
                        </div>
                        {expandedSections.analysis && (
                            <div className="p-1 space-y-2">
                                {filteredAnalysis.map((analysis) => (
                                    <ListItem
                                        key={analysis.jobId}
                                        item={analysis}
                                        type="analysis"
                                        isInContext={analysisesInContext.some((a: AnalysisJobResultMetadata) => a.jobId === analysis.jobId)}
                                        onClick={() => handleAnalysisToggle(analysis)}
                                    />
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Automations Section */}
                    <div className="border-b border-[#1a2438]">
                        <div className="flex items-center justify-between p-1 hover:bg-[#1a2438] transition-colors rounded">
                            <button
                                onClick={() => toggleSection('automations')}
                                className="flex items-center gap-2 p-2 rounded flex-1"
                            >
                                {expandedSections.automations ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                <span className="text-sm font-medium">Automations</span>
                            </button>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    {/* TODO: Implement add automation */};
                                }}
                                className="px-3 py-1.5 rounded-md border shadow-md bg-gradient-to-r from-[#1a2438] to-[#273349] text-blue-300 hover:text-white hover:from-blue-600 hover:to-blue-700 border-[#2a4170] text-xs font-medium flex items-center gap-1.5"
                                title="Add Automation"
                            >
                                <Plus size={14} />
                                <span>Add Automation</span>
                            </button>
                        </div>
                        {expandedSections.automations && (
                            <div className="p-1 space-y-2">
                                {filteredAutomations.map((automation) => (
                                    <ListItem
                                        key={automation.id}
                                        item={automation}
                                        type="automation"
                                        isInContext={false}
                                        onClick={() => {}}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <>
            <div className={`relative flex flex-col h-full bg-gray-950 border-r border-[#101827] text-white transition-all duration-300 ${isCollapsed ? 'w-12' : 'w-[300px]'}`}>
                <button
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className="absolute -right-3 top-1/2 transform -translate-y-1/2 bg-gray-950 border border-[#101827] rounded-full p-1 z-10"
                >
                    {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
                </button>

                {!isCollapsed && renderContent()}

                {isCollapsed && (
                    <div className="flex flex-col items-center pt-12 gap-4">
                        <button
                            className="p-2 rounded-lg text-zinc-400"
                            title="Datasets"
                        >
                            <Database size={20} />
                        </button>
                        <button
                            className="p-2 rounded-lg text-zinc-400"
                            title="Analysis"
                        >
                            <BarChart3 size={20} />
                        </button>
                        <button
                            className="p-2 rounded-lg text-zinc-400"
                            title="Automations"
                        >
                            <Zap size={20} />
                        </button>
                    </div>
                )}
            </div>

            <IntegrationManager
                isOpen={showIntegrationManager}
                onClose={() => setShowIntegrationManager(false)}
            />

            <AddAnalysis
                isOpen={showAddAnalysis}
                onClose={() => setShowAddAnalysis(false)}
            />
        </>
    );
}
