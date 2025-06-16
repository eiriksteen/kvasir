'use client';

import { useState, useMemo } from 'react';
import { Database, Plus, Check, Upload, Trash2, ChevronLeft, ChevronRight, FolderGit2, BarChart3, Zap, ChevronDown, ChevronUp } from 'lucide-react';
import { TimeSeriesDataset } from '@/types/datasets';
import { Automation } from '@/types/automations';
import { useAgentContext, useDatasets, useAnalysis, useProject } from '@/hooks';
import { useSession } from 'next-auth/react';
import { redirect } from 'next/navigation';
import { AnalysisJobResultMetadata } from '@/types/analysis';
import ConfirmationPopup from './ConfirmationPopup';
import SelectProject from './SelectProject';
import { Project } from '@/types/project';
import IntegrationManager from './integration/IntegrationManager';

type TabType = 'project' | 'datasets' | 'analysis' | 'automations';

function DatasetItem({ dataset, isInContext, onClick }: { dataset: TimeSeriesDataset; isInContext: boolean; onClick: () => void }) {
    return (
        <div
            onClick={onClick}
            className={`p-3 rounded-lg cursor-pointer transition-all duration-200 hover:bg-[#0a101c] border-2 ${
                isInContext ? 'bg-[#0a101c] border-[#2a4170]' : 'bg-[#050a14] border-[#101827]'
            }`}
        >
            <div className="flex justify-between items-center pr-2">
                <div className="flex-1">
                    <div className="text-sm font-medium">{dataset.name}</div>
                    <div className="text-xs text-zinc-400 flex items-center gap-1.5">
                        <span>Time Series</span>
                        {isInContext && (
                            <span className="bg-[#0e1a30] text-blue-300 text-xs px-1.5 py-0.5 rounded-full flex items-center gap-0.5">
                                <Database size={10} />
                            </span>
                        )}
                    </div>
                </div>
                
                <button 
                    onClick={(e) => {
                        e.stopPropagation();
                        onClick();
                    }}
                    className={`p-1.5 rounded-full border shadow-md ${
                        isInContext
                            ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white border-blue-500 shadow-blue-900/30'
                            : 'bg-gradient-to-r from-[#1a2438] to-[#273349] text-blue-300 hover:text-white hover:from-blue-600 hover:to-blue-700 border-[#2a4170]'
                    }`}
                    title={isInContext ? "Remove from context" : "Add to chat context"}
                >
                    {isInContext ? <Check size={14} /> : <Plus size={14} />}
                </button>
            </div>
        </div>
    );
}

function AutomationItem({ automation, isSelected, onClick }: { automation: Automation; isSelected: boolean; onClick: () => void }) {
    return (
        <div
            onClick={onClick}
            className={`p-3 rounded-lg cursor-pointer hover:bg-[#2a1c30] border-2 ${
                isSelected ? 'bg-[#2a1c30] border-purple-800' : 'bg-[#1a1625]/80 border-[#271a30]'
            }`}
        >
            <div className="text-sm font-medium">{automation.name}</div>
            <div className="text-xs text-zinc-400">{automation.description}</div>
        </div>
    );
}

function AnalysisItem({ analysis, isSelected, onClick }: {analysis: AnalysisJobResultMetadata, isSelected: boolean, onClick: () => void }) {
    const { deleteAnalysisJobResults } = useAnalysis();
    const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);

    const handleDelete = (e: React.MouseEvent) => {
        e.stopPropagation();
        setShowDeleteConfirmation(true);
    };

    const handleConfirmDelete = async () => {
        await deleteAnalysisJobResults(analysis);
        setShowDeleteConfirmation(false);
    };

    return (
        <>
            <div 
                onClick={onClick}
                className={`p-3 rounded-lg cursor-pointer hover:bg-[#1a2438] border-2 ${
                    isSelected ? 'bg-[#1a2438] border-blue-800' : 'bg-[#0e1a30]/80 border-[#1a2438]'
                }`}
            >
                <div className="flex justify-between items-start">
                    <div className="flex flex-col gap-2">
                        <div className="text-sm font-medium text-blue-300">Analysis Results</div>
                        <div className="text-xs text-zinc-400">
                            <div>Job ID: {analysis.jobId}</div>
                            <div>Datasets: {analysis.numberOfDatasets}</div>
                            <div>Automations: {analysis.numberOfAutomations}</div>
                            <div>Created: {new Date(analysis.createdAt).toLocaleDateString()}</div>
                            <div>PDF Created: {analysis.pdfCreated ? "Yes" : "No"}</div>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button 
                            onClick={handleDelete}
                            className="p-1.5 rounded-full border shadow-md bg-gradient-to-r from-red-600/40 to-red-700/40 text-red-300 border-red-500/30 shadow-red-900/20 hover:from-red-600/60 hover:to-red-700/60 hover:text-red-200"
                            title="Delete analysis"
                        >
                            <Trash2 size={14} />
                        </button>
                        <button 
                            onClick={(e) => {
                                e.stopPropagation();
                                onClick();
                            }}
                            className={`p-1.5 rounded-full border shadow-md ${
                                isSelected
                                    ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white border-blue-500 shadow-blue-900/30'
                                    : 'bg-gradient-to-r from-[#1a2438] to-[#273349] text-blue-300 hover:text-white hover:from-blue-600 hover:to-blue-700 border-[#2a4170]'
                            }`}
                            title={isSelected ? "Remove from context" : "Add to chat context"}
                        >
                            {isSelected ? <Check size={14} /> : <Plus size={14} />}
                        </button>
                    </div>
                </div>
            </div>
            <ConfirmationPopup
                isOpen={showDeleteConfirmation}
                message={`Are you sure you want to delete this analysis? This action cannot be undone.`}
                onConfirm={handleConfirmDelete}
                onCancel={() => setShowDeleteConfirmation(false)}
            />
        </>
    );
}

export default function OntologyBar() {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [showAddProject, setShowAddProject] = useState(false);
    const [showIntegrationManager, setShowIntegrationManager] = useState(false);
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
    console.log("analysisJobResults", datasets);

    // Filter entities based on project IDs
    // const filteredDatasets = useMemo(() => {
    //     if (!selectedProject || !datasets?.timeSeries) return [];
    //     return datasets.timeSeries.filter(dataset => 
    //         selectedProject.datasetIds.includes(dataset.id)
    //     );
    // }, [selectedProject, datasets]);

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

    const handleSelectProject = (project: Project) => {
        setShowAddProject(false);
    };

    const renderContent = () => {
        if (!selectedProject) {
            return (
                <div className="flex flex-col h-full items-center justify-center p-4">
                    <p className="text-sm text-zinc-400 mb-4">No project selected</p>
                    <button
                        onClick={() => setShowAddProject(true)}
                        className="w-full px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-md hover:from-blue-500 hover:to-blue-600 transition-all shadow-md hover:shadow-lg border border-blue-500 flex items-center justify-center gap-2"
                    >
                        <Plus size={16} />
                        <span>Select Project</span>
                    </button>
                </div>
            );
        }

        return (
            console.log("selectedProject", selectedProject),
            <div className="flex flex-col h-full">
                <button
                    onClick={() => setShowAddProject(true)}
                    className="w-full p-3 bg-[#111827] border-b border-[#1a2438] text-left hover:bg-[#1a2438] transition-colors"
                >
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <FolderGit2 size={16} className="text-blue-400" />
                            <span className="text-sm font-medium">{selectedProject.name}</span>
                        </div>
                        <ChevronRight size={16} className="text-zinc-400" />
                    </div>
                </button>

                <div className="flex-1 overflow-y-auto">
                    {/* Datasets Section */}
                    <div className="border-b border-[#1a2438]">
                        <div className="flex items-center justify-between p-3">
                            <button
                                onClick={() => toggleSection('datasets')}
                                className="flex items-center gap-2 hover:bg-[#1a2438] transition-colors p-2 rounded"
                            >
                                <Database size={16} className="text-blue-400" />
                                <span className="text-sm font-medium">Datasets</span>
                                {expandedSections.datasets ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            </button>
                            <button
                                onClick={() => setShowIntegrationManager(true)}
                                className="p-1.5 rounded-full border shadow-md bg-gradient-to-r from-[#1a2438] to-[#273349] text-blue-300 hover:text-white hover:from-blue-600 hover:to-blue-700 border-[#2a4170]"
                                title="Add Dataset"
                            >
                                <Plus size={14} />
                            </button>
                        </div>
                        {expandedSections.datasets && (
                            <div className="p-3 space-y-2">
                                {datasets?.timeSeries
                                    .filter(dataset => selectedProject.datasetIds.includes(dataset.id))
                                    .map((dataset) => (
                                        <DatasetItem 
                                            key={dataset.id}
                                            dataset={dataset}
                                            isInContext={isDatasetInContext(dataset.id)}
                                            onClick={() => handleDatasetToggle(dataset)}
                                        />
                                    ))}
                            </div>
                        )}
                    </div>

                    {/* Analysis Section */}
                    <div className="border-b border-[#1a2438]">
                        <div className="flex items-center justify-between p-3">
                            <button
                                onClick={() => toggleSection('analysis')}
                                className="flex items-center gap-2 hover:bg-[#1a2438] transition-colors p-2 rounded"
                            >
                                <BarChart3 size={16} className="text-blue-400" />
                                <span className="text-sm font-medium">Analysis</span>
                                {expandedSections.analysis ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            </button>
                            <button
                                onClick={() => {/* TODO: Implement add analysis */}}
                                className="p-1.5 rounded-full border shadow-md bg-gradient-to-r from-[#1a2438] to-[#273349] text-blue-300 hover:text-white hover:from-blue-600 hover:to-blue-700 border-[#2a4170]"
                                title="Add Analysis"
                            >
                                <Plus size={14} />
                            </button>
                        </div>
                        {expandedSections.analysis && (
                            <div className="p-3 space-y-2">
                                {filteredAnalysis.map((analysis) => (
                                    <AnalysisItem
                                        key={analysis.jobId}
                                        analysis={analysis}
                                        isSelected={analysisesInContext.some((a: AnalysisJobResultMetadata) => a.jobId === analysis.jobId)}
                                        onClick={() => handleAnalysisToggle(analysis)}
                                    />
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Automations Section */}
                    <div className="border-b border-[#1a2438]">
                        <div className="flex items-center justify-between p-3">
                            <button
                                onClick={() => toggleSection('automations')}
                                className="flex items-center gap-2 hover:bg-[#1a2438] transition-colors p-2 rounded"
                            >
                                <Zap size={16} className="text-blue-400" />
                                <span className="text-sm font-medium">Automations</span>
                                {expandedSections.automations ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            </button>
                            <button
                                onClick={() => {/* TODO: Implement add automation */}}
                                className="p-1.5 rounded-full border shadow-md bg-gradient-to-r from-[#1a2438] to-[#273349] text-blue-300 hover:text-white hover:from-blue-600 hover:to-blue-700 border-[#2a4170]"
                                title="Add Automation"
                            >
                                <Plus size={14} />
                            </button>
                        </div>
                        {expandedSections.automations && (
                            <div className="p-3 space-y-2">
                                {filteredAutomations.map((automation) => (
                                    <AutomationItem
                                        key={automation.id}
                                        automation={automation}
                                        isSelected={false}
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
                            onClick={() => setShowAddProject(true)}
                            className={`p-2 rounded-lg ${!selectedProject ? 'bg-[#1a2438] text-blue-400' : 'text-zinc-400'}`}
                            title="Select Project"
                        >
                            <FolderGit2 size={20} />
                        </button>
                        {selectedProject && (
                            <>
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
                            </>
                        )}
                    </div>
                )}
            </div>

            {showAddProject && (
                <SelectProject
                    onSelect={handleSelectProject}
                />
            )}

            <IntegrationManager
                isOpen={showIntegrationManager}
                onClose={() => setShowIntegrationManager(false)}
            />
        </>
    );
}
