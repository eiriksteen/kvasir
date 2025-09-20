'use client';

import React from 'react';
import { useState } from 'react';
import { Database, ChevronLeft, ChevronRight, BarChart3, Zap, Folder, Package, Brain } from 'lucide-react';
import { Dataset } from '@/types/data-objects';
import { useAgentContext, useDatasets, useModelSources, usePipelines, useProject } from '@/hooks';
import { useSession } from 'next-auth/react';
import { redirect } from 'next/navigation';
import { AnalysisJobResultMetadata } from '@/types/analysis';
import AddDataSource from '@/app/projects/[projectId]/_components/add-entity-modals/AddDataSource';
import AddAnalysis from '@/app/projects/[projectId]/_components/add-entity-modals/AddAnalysis';
import { useProjectDataSources } from '@/hooks/useDataSources';
import { DataSource } from '@/types/data-sources';
import EntityItem from '@/app/projects/[projectId]/_components/entity-sidebar/EntityItem';
import AddEntityButton from '@/app/projects/[projectId]/_components/entity-sidebar/AddEntityButton';
import EntityOverviewItem from '@/app/projects/[projectId]/_components/entity-sidebar/EntityOverviewItem';
import { UUID } from 'crypto';
import AddDataset from '@/app/projects/[projectId]/_components/add-entity-modals/AddDataset';
import AddPipeline from '@/app/projects/[projectId]/_components/add-entity-modals/AddPipeline';
import { Pipeline } from '@/types/pipeline';
import { useModelEntities } from '@/hooks/useModelEntities';
import { ModelSource } from '@/types/model-source';
import { ModelEntity } from '@/types/model';
import AddModelSource from '@/app/projects/[projectId]/_components/add-entity-modals/AddModelSource';
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
    const [showAddModelSourceToProject, setShowAddModelSourceToProject] = useState(false);
    const [showAddModelToProject, setShowAddModelToProject] = useState(false);
    const [expandedSections, setExpandedSections] = useState({
        datasets: false,
        analysis: false,
        pipelines: false,
        data_sources: false,
        model_sources: false,
        models: false
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
        removeAnalysisFromContext,
        pipelinesInContext,
        addPipelineToContext,
        removePipelineFromContext,
        modelSourcesInContext,
        addModelSourceToContext,
        removeModelSourceFromContext,
        modelsInContext,
        addModelToContext,
        removeModelFromContext,

    } = useAgentContext(projectId);  

    if (!session) {
        redirect("/login");
    }

    const { datasets } = useDatasets(projectId);
    const { dataSources } = useProjectDataSources(projectId);
    const { pipelines } = usePipelines(projectId);
    const { models } = useModelEntities(projectId);
    const { modelSources } = useModelSources(projectId);
    const analyses: AnalysisJobResultMetadata[] = []


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

    const handlePipelineToggle = (pipeline: Pipeline) => {

        const isActive = pipelinesInContext.some((p: Pipeline) => p.id === pipeline.id);
        if (isActive) {
            removePipelineFromContext(pipeline);
        } else {
            addPipelineToContext(pipeline);
        }
    };

    const handleModelSourceToggle = (modelSource: ModelSource) => {
        const isActive = modelSourcesInContext.some((m: ModelSource) => m.id === modelSource.id);
        if (isActive) {
            removeModelSourceFromContext(modelSource);
        } else {
            addModelSourceToContext(modelSource);
        }
    };

    const handleModelToggle = (model: ModelEntity) => {
        const isActive = modelsInContext.some((m: ModelEntity) => m.id === model.id);
        if (isActive) {
            removeModelFromContext(model);
        } else {
            addModelToContext(model);
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
                    <div className="p-4">
                        <h3 className='text-xs font-mono uppercase tracking-wider text-gray-400'> SOURCES </h3>
                    </div>

                    {/* Data Sources Section */}
                    <div className="border-b border-gray-800">
                        <EntityOverviewItem
                            title="Data Sources"
                            count={dataSources?.length || 0}
                            color="emerald"
                            onToggle={() => toggleSection('data_sources')}
                            onAdd={() => setShowAddDataSourceToProject(true)}
                        />
                        {expandedSections.data_sources && (
                            <div className="bg-emerald-500/5 border-l-2 border-emerald-500/20">
                                {dataSources?.map((dataSource) => (
                                    <EntityItem
                                        key={dataSource.id}
                                        item={dataSource}
                                        type="data_source"
                                        isInContext={dataSourcesInContext.some((d: DataSource) => d.id === dataSource.id)}
                                        onClick={() => handleDataSourceToggle(dataSource)}
                                    />
                                ))}
                                {dataSources?.length === 0 && (
                                    <div className="px-3 py-4 text-center">
                                        <Database size={16} className="text-emerald-400/40 mx-auto mb-2" />
                                        <p className="text-xs text-gray-500">No data sources</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Model Sources Section */}
                    <div className="border-b border-gray-800">
                        <EntityOverviewItem
                            title="Model Sources"
                            count={modelSources?.length || 0}
                            color="emerald"
                            onToggle={() => toggleSection('model_sources')}
                            onAdd={() => setShowAddModelSourceToProject(true)}
                        />
                    </div>
                    {expandedSections.model_sources && (
                        <div className="bg-emerald-500/5 border-l-2 border-emerald-500/20">
                            {modelSources?.map((modelSource) => (
                                <EntityItem key={modelSource.id} item={modelSource} type="model_source" isInContext={modelSourcesInContext.some((m: ModelSource) => m.id === modelSource.id)} onClick={() => handleModelSourceToggle(modelSource)} />
                            ))}
                            {modelSources?.length === 0 && (
                                <div className="px-3 py-4 text-center">
                                    <Package size={16} className="text-emerald-400/40 mx-auto mb-2" />
                                    <p className="text-xs text-gray-500">No model sources</p>
                                </div>
                            )}
                        </div>
                    )}

                    <div className="p-4">
                        <h3 className='text-xs font-mono uppercase tracking-wider text-gray-400'> ENTITIES </h3>
                    </div>

                    {/* Datasets Section */}
                    <div className="border-b border-gray-800">
                        <EntityOverviewItem
                            title="Datasets"
                            count={datasets?.length || 0}
                            color="blue"
                            onToggle={() => toggleSection('datasets')}
                            onAdd={() => setShowAddDatasetToProject(true)}
                        />
                        {datasets && expandedSections.datasets && (
                            <div className="bg-blue-500/5 border-l-2 border-blue-500/20">
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
                                        <Folder size={16} className="text-blue-400/40 mx-auto mb-2" />
                                        <p className="text-xs text-gray-500">No datasets</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Models Section */}
                    <div className="border-b border-gray-800">
                        <EntityOverviewItem
                            title="Models"
                            count={models?.length || 0}
                            color="emerald"
                            onToggle={() => toggleSection('models')}
                            onAdd={() => setShowAddModelToProject(true)}
                        />
                        {models && expandedSections.models && (
                            <div className="bg-emerald-500/5 border-l-2 border-emerald-500/20">
                                {models.map((model) => (
                                    <EntityItem key={model.id} item={model} type="model" isInContext={modelsInContext.some((m: ModelEntity) => m.id === model.id)} onClick={() => handleModelToggle(model)} />
                                ))}
                                {models.length === 0 && (
                                    <div className="px-3 py-4 text-center">
                                        <Brain size={16} className="text-emerald-400/40 mx-auto mb-2" />
                                        <p className="text-xs text-gray-500">No models</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Analysis Section */}
                    <div className="border-b border-gray-800">
                        <EntityOverviewItem
                            title="Analysis"
                            count={analyses.length}
                            color="purple"
                            onToggle={() => toggleSection('analysis')}
                            onAdd={() => setShowAddAnalysis(true)}
                        />
                        {expandedSections.analysis && (
                            <div className="bg-purple-500/5 border-l-2 border-purple-500/20">
                                {analyses.map((analysis) => (
                                    <EntityItem
                                        key={analysis.jobId}
                                        item={analysis}
                                        type="analysis"
                                        isInContext={analysesInContext.some((a: AnalysisJobResultMetadata) => a.jobId === analysis.jobId)}
                                        onClick={() => handleAnalysisToggle(analysis)}
                                    />
                                ))}
                                {analyses.length === 0 && (
                                    <div className="px-3 py-4 text-center">
                                        <BarChart3 size={16} className="text-purple-400/40 mx-auto mb-2" />
                                        <p className="text-xs text-gray-500">No analysis</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Pipeline Section */}
                    <div className="border-b border-gray-800">
                        <EntityOverviewItem
                            title="Pipelines"
                            count={pipelines?.length || 0}
                            color="orange"
                            onToggle={() => toggleSection('pipelines')}
                            onAdd={() => setShowAddPipeline(true)}
                        />
                        {pipelines && expandedSections.pipelines && (
                            <div className="bg-orange-500/5 border-l-2 border-orange-500/20">
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
                                        <Zap size={16} className="text-orange-400/40 mx-auto mb-2" />
                                        <p className="text-xs text-gray-500">No pipelines</p>
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
                            <AddEntityButton type="data_source" size={14} onAdd={() => setShowAddDataSourceToProject(true)} />
                            <AddEntityButton type="model_source" size={14} onAdd={() => setShowAddModelSourceToProject(true)} />

                            <div className="w-6 h-px bg-gray-700 my-4"></div>

                            <AddEntityButton type="dataset" size={14} onAdd={() => setShowAddDatasetToProject(true)} />
                            <AddEntityButton type="model" size={14} onAdd={() => setShowAddModelToProject(true)} />
                            <AddEntityButton type="analysis" size={14} onAdd={() => setShowAddAnalysis(true)} />
                            <AddEntityButton type="pipeline" size={14} onAdd={() => setShowAddPipeline(true)} />
             
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

            {showAddPipeline && <AddPipeline
                onClose={() => setShowAddPipeline(false)}
                projectId={projectId}
            />}

            {showAddModelSourceToProject && <AddModelSource
                onClose={() => setShowAddModelSourceToProject(false)}
                projectId={projectId}
            />}

            {showAddModelToProject && <AddModelEntity   
                onClose={() => setShowAddModelToProject(false)}
                projectId={projectId}
            />}
        </div>
    );
}