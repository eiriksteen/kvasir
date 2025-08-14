'use client';

import React from 'react';
import { useState, useMemo } from 'react';
import { Database, ChevronLeft, ChevronRight, BarChart3, Zap, Folder } from 'lucide-react';
import { Dataset } from '@/types/data-objects';
import { Automation } from '@/types/automation';
import { useAgentContext, useDatasets, useProject } from '@/hooks';
import { useSession } from 'next-auth/react';
import { redirect } from 'next/navigation';
import { AnalysisJobResultMetadata } from '@/types/analysis';
import AddDataSource from '@/app/projects/[projectId]/_components/add-entity-modals/AddDataSource';
import AddAnalysis from '@/app/projects/[projectId]/_components/add-entity-modals/AddAnalysis';
import { useDataSources } from '@/hooks/useDataSources';
import { DataSource } from '@/types/data-sources';
import EntityItem from '@/app/projects/[projectId]/_components/entity-sidebar/EntityItem';
import AddEntityIcon from '@/app/projects/[projectId]/_components/entity-sidebar/AddEntityIcon';
import EntityOverviewItem from '@/app/projects/[projectId]/_components/entity-sidebar/EntityOverviewItem';
import { UUID } from 'crypto';
import AddDataset from '@/app/projects/[projectId]/_components/add-entity-modals/AddDataset';
import AddAutomation from '@/app/projects/[projectId]/_components/add-entity-modals/AddAutomation';

interface EntitySidebarProps {
    projectId: UUID;
}

export default function EntitySidebar({ projectId }: EntitySidebarProps) {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [showAddDataSourceToProject, setShowAddDataSourceToProject] = useState(false);
    const [showAddAnalysis, setShowAddAnalysis] = useState(false);
    const [showAddDatasetToProject, setShowAddDatasetToProject] = useState(false);
    const [showAddAutomation, setShowAddAutomation] = useState(false);
    const [expandedSections, setExpandedSections] = useState({
        datasets: false,
        analysis: false,
        automations: false,
        data_sources: false
    });
    const { data: session } = useSession();
    const { project } = useProject(projectId);
    const { 
        dataSourcesInContext,
        addDataSourceToContext,
        removeDataSourceFromContext,
        datasetsInContext, 
        addDatasetToContext, 
        removeDatasetFromContext,
        analysesInContext,
        addAnalysisToContext,
        removeAnalysisFromContext
    } = useAgentContext(projectId);  

    if (!session) {
        redirect("/login");
    }

    const { datasets } = useDatasets();
    const { dataSources } = useDataSources();
    const automations: Automation[] = [];
    // const { analysisJobResults } = useAnalysis();

    const filteredDataSources = useMemo(() => {
        if (!project || !dataSources) return [];
        return dataSources.filter(dataSource => 
            project.dataSourceIds.includes(dataSource.id)
        );
    }, [project, dataSources]);

    const filteredDatasets = useMemo(() => {
        if (!project || !datasets) return [];
        return datasets.filter(dataset => 
            project.datasetIds.includes(dataset.id)
        );
    }, [project, datasets]);

    const filteredAnalysis: AnalysisJobResultMetadata[] = []

    const filteredAutomations = useMemo(() => {
        if (!project || !automations) return [];
        return automations.filter(automation => 
            project.automationIds.includes(automation.id)
        );
    }, [project, automations]);

    const toggleSection = (section: keyof typeof expandedSections) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    const handleDataSourceToggle = (dataSource: DataSource) => {
        const isActive = dataSourcesInContext.some((d: DataSource) => d.id === dataSource.id);
        if (isActive) {
            removeDataSourceFromContext(dataSource);
        } else {
            addDataSourceToContext(dataSource);
        }
    };

    const handleDatasetToggle = (dataset: Dataset) => {
        const isActive = datasetsInContext.some((d: Dataset) => d.id === dataset.id);
        if (isActive) {
            removeDatasetFromContext(dataset);
        } else {
            addDatasetToContext(dataset);
        }
    };

    const handleAnalysisToggle = (analysis: AnalysisJobResultMetadata) => {
        const isActive = analysesInContext.some((a: AnalysisJobResultMetadata) => a.jobId === analysis.jobId);
        if (isActive) {
            removeAnalysisFromContext(analysis);
        } else {
            addAnalysisToContext(analysis);
        }
    };

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

                <div className="flex-1 overflow-y-auto">

                    {/* Data Sources Section */}
                    <div className="border-b border-gray-800">
                        <EntityOverviewItem
                            title="Data Sources"
                            count={filteredDataSources?.length || 0}
                            color="emerald"
                            onToggle={() => toggleSection('data_sources')}
                            onAdd={() => setShowAddDataSourceToProject(true)}
                        />
                        {expandedSections.data_sources && (
                            <div className="bg-emerald-500/5 border-l-2 border-emerald-500/20">
                                {filteredDataSources?.map((dataSource) => (
                                    <EntityItem
                                        key={dataSource.id}
                                        item={dataSource}
                                        type="data_source"
                                        isInContext={dataSourcesInContext.some((d: DataSource) => d.id === dataSource.id)}
                                        onClick={() => handleDataSourceToggle(dataSource)}
                                    />
                                ))}
                                {filteredDataSources?.length === 0 && (
                                    <div className="px-3 py-4 text-center">
                                        <Database size={16} className="text-emerald-400/40 mx-auto mb-2" />
                                        <p className="text-xs text-gray-500">No data sources</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Datasets Section */}
                    <div className="border-b border-gray-800">
                        <EntityOverviewItem
                            title="Datasets"
                            count={filteredDatasets?.length || 0}
                            color="blue"
                            onToggle={() => toggleSection('datasets')}
                            onAdd={() => setShowAddDatasetToProject(true)}
                        />
                        {expandedSections.datasets && (
                            <div className="bg-blue-500/5 border-l-2 border-blue-500/20">
                                {filteredDatasets
                                    .map((dataset) => (
                                        <EntityItem 
                                            key={dataset.id}
                                            item={dataset}
                                            type="dataset"
                                            isInContext={datasetsInContext.some((d: Dataset) => d.id === dataset.id)}
                                            onClick={() => handleDatasetToggle(dataset)}
                                        />
                                    ))}
                                {filteredDatasets.length === 0 && (
                                    <div className="px-3 py-4 text-center">
                                        <Folder size={16} className="text-blue-400/40 mx-auto mb-2" />
                                        <p className="text-xs text-gray-500">No datasets</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Analysis Section */}
                    <div className="border-b border-gray-800">
                        <EntityOverviewItem
                            title="Analysis"
                            count={filteredAnalysis.length}
                            color="purple"
                            onToggle={() => toggleSection('analysis')}
                            onAdd={() => setShowAddAnalysis(true)}
                        />
                        {expandedSections.analysis && (
                            <div className="bg-purple-500/5 border-l-2 border-purple-500/20">
                                {filteredAnalysis.map((analysis) => (
                                    <EntityItem
                                        key={analysis.jobId}
                                        item={analysis}
                                        type="analysis"
                                        isInContext={analysesInContext.some((a: AnalysisJobResultMetadata) => a.jobId === analysis.jobId)}
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
                        <EntityOverviewItem
                            title="Automations"
                            count={filteredAutomations.length}
                            color="orange"
                            onToggle={() => toggleSection('automations')}
                            onAdd={() => setShowAddAutomation(true)}
                        />
                        {expandedSections.automations && (
                            <div className="bg-orange-500/5 border-l-2 border-orange-500/20">
                                {filteredAutomations.map((automation) => (
                                    <EntityItem
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
                    <div className="flex items-center justify-end px-3 py-2">
                    <button
                        onClick={() => setIsCollapsed(!isCollapsed)}
                        className="p-2 rounded-full text-gray-400 hover:text-white hover:bg-gray-800 bg-gray-900/50 border border-gray-800"
                        title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                    >
                        {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
                    </button>
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
                        {/* Collapsed content */}
                        <div className="flex flex-col items-center pt-3 gap-2">
                            <button
                                onClick={() => setShowAddDataSourceToProject(true)}
                                className="p-2 rounded-md text-emerald-400 hover:text-emerald-300 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 hover:border-emerald-500/40 transition-all duration-200 hover:scale-105"
                                title="Add Data Source"
                            >
                                <AddEntityIcon type="data_source" size={14} />
                            </button>
                            <button
                                onClick={() => setShowAddDatasetToProject(true)}
                                className="p-2 rounded-md text-blue-400 hover:text-blue-300 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 hover:border-blue-500/40 transition-all duration-200 hover:scale-105"
                                title="Add Dataset to Project"
                            >
                                <AddEntityIcon type="dataset" size={14} />
                            </button>
                            <button
                                onClick={() => setShowAddAnalysis(true)}
                                className="p-2 rounded-md text-purple-400 hover:text-purple-300 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/20 hover:border-purple-500/40 transition-all duration-200 hover:scale-105"
                                title="Add Analysis"
                            >
                                <AddEntityIcon type="analysis" size={14} />
                            </button>
                            <button
                                onClick={() => setShowAddAutomation(true)}
                                className="p-2 rounded-md text-orange-400 hover:text-orange-300 bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/20 hover:border-orange-500/40 transition-all duration-200 hover:scale-105"
                                title="Add Automation"
                            >
                                <AddEntityIcon type="automation" size={14} />
                            </button>
                        </div>
                        
                        {/* Collapse/expand button at bottom */}
                        <div className="flex items-center justify-center px-3 py-2 mt-auto">
                            <button
                                onClick={() => setIsCollapsed(!isCollapsed)}
                                className="p-2 rounded-full text-gray-400 hover:text-white hover:bg-gray-800 bg-gray-900/50 border border-gray-800"
                                title="Expand sidebar"
                            >
                                <ChevronRight size={14} />
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {showAddDataSourceToProject && <AddDataSource
                onClose={() => setShowAddDataSourceToProject(false)}
                projectId={projectId}
            />}

            {showAddAnalysis && <AddAnalysis
                onClose={() => setShowAddAnalysis(false)}
                projectId={projectId}
            />}

            {showAddDatasetToProject && <AddDataset
                onClose={() => setShowAddDatasetToProject(false)}
                projectId={projectId}
            />}

            {showAddAutomation && <AddAutomation
                onClose={() => setShowAddAutomation(false)}
                projectId={projectId}
            />}
        </div>
    );
}
