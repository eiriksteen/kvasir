'use client';

import React from 'react';
import { useState } from 'react';
import { ChevronLeft, ChevronRight, BarChart3, Zap, Folder, Brain, Database } from 'lucide-react';
import { Dataset } from '@/types/data-objects';
import { DataSource } from '@/types/data-sources';
import { useAgentContext, useAnalysis, useDatasets, usePipelines, useProject, useProjectDataSources } from '@/hooks';
import { useSession } from 'next-auth/react';
import { redirect } from 'next/navigation';
import { AnalysisObjectSmall } from '@/types/analysis';
import AddDataSource from '@/app/projects/[projectId]/_components/add-entity-modals/AddDataSource';
import AddAnalysis from '@/app/projects/[projectId]/_components/add-entity-modals/AddAnalysis';
import EntityItem from '@/app/projects/[projectId]/_components/entity-sidebar/EntityItem';
import AddEntityButton from '@/app/projects/[projectId]/_components/entity-sidebar/AddEntityButton';
import EntityOverviewItem from '@/app/projects/[projectId]/_components/entity-sidebar/EntityOverviewItem';
import { UUID } from 'crypto';
import AddDataset from '@/app/projects/[projectId]/_components/add-entity-modals/AddDataset';
import AddPipeline from '@/app/projects/[projectId]/_components/add-entity-modals/AddPipeline';
import { Pipeline } from '@/types/pipeline';
import { useModelEntities } from '@/hooks/useModelEntities';
import { ModelEntity } from '@/types/model';
import AddModelEntity from '@/app/projects/[projectId]/_components/add-entity-modals/AddModelEntity';


interface EntitySidebarProps {
    projectId: UUID;
}

export default function EntitySidebar({ projectId }: EntitySidebarProps) {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [showAddDataSourceToProject, setShowAddDataSourceToProject] = useState(false);
    const [showAddAnalysis, setShowAddAnalysis] = useState(false);
    const [showAddDatasetToProject, setShowAddDatasetToProject] = useState(false);
    const [showAddPipeline, setShowAddPipeline] = useState(false);
    const [showAddModelToProject, setShowAddModelToProject] = useState(false);
    const [expandedSections, setExpandedSections] = useState({
        dataSources: false,
        datasets: false,
        analysis: false,
        pipelines: false,
        models: false
    });
    const [showEntities, setShowEntities] = useState(true);
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
        removeAnalysisFromContext,
        pipelinesInContext,
        addPipelineToContext,
        removePipelineFromContext,
        modelEntitiesInContext,
        addModelEntityToContext,
        removeModelEntityFromContext,

    } = useAgentContext(projectId);  

    if (!session) {
        redirect("/login");
    }

    const { dataSources } = useProjectDataSources(projectId);
    const { datasets } = useDatasets(projectId);
    const { pipelines } = usePipelines(projectId);
    const { modelEntities } = useModelEntities(projectId);
    const { analysisObjects } = useAnalysis(projectId);

    const toggleSection = (section: keyof typeof expandedSections) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    const handleDatasetToggle = (dataset: Dataset) => {
        const isActive = datasetsInContext.some((d: Dataset) => d.id === dataset.id);
        if (isActive) {
            removeDatasetFromContext(dataset);
        } else {
            addDatasetToContext(dataset);
        }
    };

    const handleDataSourceToggle = (dataSource: DataSource) => {
        const isActive = dataSourcesInContext.some((ds: DataSource) => ds.id === dataSource.id);
        if (isActive) {
            removeDataSourceFromContext(dataSource);
        } else {
            addDataSourceToContext(dataSource);
        }
    };

    const handleAnalysisToggle = (analysis: AnalysisObjectSmall) => {
        const isActive = analysesInContext.some((a: AnalysisObjectSmall) => a.id === analysis.id);
        if (isActive) {
            removeAnalysisFromContext(analysis);
        } else {
            addAnalysisToContext(analysis);
        }
    };

    const handlePipelineToggle = (pipeline: Pipeline) => {

        const isActive = pipelinesInContext.some((p: Pipeline) => p.id === pipeline.id);
        if (isActive) {
            removePipelineFromContext(pipeline);
        } else {
            addPipelineToContext(pipeline);
        }
    };

    const handleModelToggle = (model: ModelEntity) => {
        const isActive = modelEntitiesInContext.some((m: ModelEntity) => m.id === model.id);
        if (isActive) {
            removeModelEntityFromContext(model);
        } else {
            addModelEntityToContext(model);
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
                    <div className="border-b border-gray-400">
                        <div className="flex items-center justify-between pl-4 pr-3 pt-2 pb-2 bg-gray-100 cursor-pointer hover:bg-gray-200 transition-colors" onClick={() => toggleSection('dataSources')}>
                            <h3 className='text-xs font-mono uppercase tracking-wider text-gray-900'> DATA SOURCES </h3>
                            <AddEntityButton type="data_source" size={14} onAdd={() => setShowAddDataSourceToProject(true)} />
                        </div>
                        {dataSources && expandedSections.dataSources && (
                            <div className="bg-gray-50 border-l-2 border-gray-600">
                                {dataSources.map((dataSource) => (
                                    <EntityItem
                                        key={dataSource.id}
                                        item={dataSource}
                                        type="data_source"
                                        isInContext={dataSourcesInContext.some((ds: DataSource) => ds.id === dataSource.id)}
                                        onClick={() => handleDataSourceToggle(dataSource)}
                                    />
                                ))}
                                {dataSources.length === 0 && (
                                    <div className="px-3 py-4 text-center">
                                        <Database size={16} className="text-gray-400 mx-auto mb-2" />
                                        <p className="text-xs text-gray-500">No data sources</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    <div className="pl-4 pt-4 pb-4 border-b border-gray-400 bg-gray-100 cursor-pointer hover:bg-gray-200 transition-colors" onClick={() => setShowEntities(!showEntities)}>
                        <h3 className='text-xs font-mono uppercase tracking-wider text-gray-900'> ENTITIES </h3>
                    </div>

                    {showEntities && (
                        <>
                    {/* Datasets Section */}
                    <div className="border-b border-gray-200">
                        <EntityOverviewItem
                            title="Datasets"
                            count={datasets?.length || 0}
                            color="blue"
                            onToggle={() => toggleSection('datasets')}
                            onAdd={() => setShowAddDatasetToProject(true)}
                        />
                        {datasets && expandedSections.datasets && (
                            <div className="bg-[#0E4F70]/10 border-l-2 border-[#0E4F70]">
                                {datasets
                                    .map((dataset) => (
                                        <EntityItem 
                                            key={dataset.id}
                                            item={dataset}
                                            type="dataset"
                                            isInContext={datasetsInContext.some((d: Dataset) => d.id === dataset.id)}
                                            onClick={() => handleDatasetToggle(dataset)}
                                        />
                                    ))}
                                {datasets.length === 0 && (
                                    <div className="px-3 py-4 text-center">
                                        <Folder size={16} className="text-[#0E4F70]/40 mx-auto mb-2" />
                                        <p className="text-xs text-gray-500">No datasets</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Models Section */}
                    <div className="border-b border-gray-200">
                        <EntityOverviewItem
                            title="Models"
                            count={modelEntities?.length || 0}
                            color="emerald"
                            onToggle={() => toggleSection('models')}
                            onAdd={() => setShowAddModelToProject(true)}
                        />
                        {modelEntities && expandedSections.models && (
                            <div className="bg-[#491A32]/10 border-l-2 border-[#491A32]">
                                {modelEntities.map((model) => (
                                    <EntityItem key={model.id} item={model} type="model_entity" isInContext={modelEntitiesInContext.some((m: ModelEntity) => m.id === model.id)} onClick={() => handleModelToggle(model)} />
                                ))}
                                {modelEntities.length === 0 && (
                                    <div className="px-3 py-4 text-center">
                                        <Brain size={16} className="text-[#491A32]/40 mx-auto mb-2" />
                                        <p className="text-xs text-gray-500">No models</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Analysis Section */}
                    <div className="border-b border-gray-200">
                        <EntityOverviewItem
                            title="Analyses"
                            count={analysisObjects.analysisObjects.length}
                            color="purple"
                            onToggle={() => toggleSection('analysis')}
                            onAdd={() => setShowAddAnalysis(true)}
                        />
                        {expandedSections.analysis && (
                            <div className="bg-[#004806]/10 border-l-2 border-[#004806]">
                                {analysisObjects.analysisObjects.map((analysis) => (
                                    <EntityItem
                                        key={analysis.id}
                                        item={analysis}
                                        type="analysis"
                                        isInContext={analysesInContext.some((a: AnalysisObjectSmall) => a.id === analysis.id)}
                                        onClick={() => handleAnalysisToggle(analysis)}
                                    />
                                ))}
                                {analysisObjects.analysisObjects.length === 0 && (
                                    <div className="px-3 py-4 text-center">
                                        <BarChart3 size={16} className="text-[#004806]/40 mx-auto mb-2" />
                                        <p className="text-xs text-gray-500">No analysis</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Pipeline Section */}
                    <div className="border-b border-gray-200">
                        <EntityOverviewItem
                            title="Pipelines"
                            count={pipelines?.length || 0}
                            color="orange"
                            onToggle={() => toggleSection('pipelines')}
                            onAdd={() => setShowAddPipeline(true)}
                        />
                        {pipelines && expandedSections.pipelines && (
                            <div className="bg-[#840B08]/10 border-l-2 border-[#840B08]">
                                {pipelines.map((pipeline) => (
                                    <EntityItem
                                        key={pipeline.id}
                                        item={pipeline}
                                        type="pipeline"
                                        isInContext={pipelinesInContext.some((p: Pipeline) => p.id === pipeline.id)}
                                        onClick={() => handlePipelineToggle(pipeline)}
                                    />
                                ))}
                                {pipelines.length === 0 && (
                                    <div className="px-3 py-4 text-center">
                                        <Zap size={16} className="text-[#840B08]/40 mx-auto mb-2" />
                                        <p className="text-xs text-gray-500">No pipelines</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                        </>
                    )}
                </div>
                    <div className="flex items-center justify-end px-3 py-2">
                    <button
                        onClick={() => setIsCollapsed(!isCollapsed)}
                        className="p-2 rounded-full text-white hover:bg-[#000066] border border-gray-400 bg-[#000034]"
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
            <div className={`flex flex-col h-full bg-gray-100 border-r border-gray-200 text-gray-800 transition-all duration-300 ${isCollapsed ? 'w-10' : 'w-[260px]'}`}>
                {!isCollapsed && renderContent()}

                {isCollapsed && (
                    <div className="flex flex-col h-full">
                        {/* Data Source button at top */}
                        <div className="flex flex-col items-center pt-3">
                            <AddEntityButton type="data_source" size={14} onAdd={() => setShowAddDataSourceToProject(true)} />
                        </div>

                        {/* Centered entity buttons */}
                        <div className="flex-1 flex flex-col items-center justify-center gap-2">
                            <AddEntityButton type="dataset" size={14} onAdd={() => setShowAddDatasetToProject(true)} />
                            <AddEntityButton type="model_entity" size={14} onAdd={() => setShowAddModelToProject(true)} />
                            <AddEntityButton type="analysis" size={14} onAdd={() => setShowAddAnalysis(true)} />
                            <AddEntityButton type="pipeline" size={14} onAdd={() => setShowAddPipeline(true)} />
                        </div>

                        {/* Collapse/expand button at bottom */}
                        <div className="flex items-center justify-center px-3 py-2">
                            <button
                                onClick={() => setIsCollapsed(!isCollapsed)}
                                className="p-2 rounded-full text-white hover:bg-[#000066] border border-gray-400 bg-[#000034]"
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

            {showAddPipeline && <AddPipeline
                onClose={() => setShowAddPipeline(false)}
                projectId={projectId}
            />}

            {showAddModelToProject && <AddModelEntity   
                onClose={() => setShowAddModelToProject(false)}
                projectId={projectId}
            />}
        </div>
    );
}