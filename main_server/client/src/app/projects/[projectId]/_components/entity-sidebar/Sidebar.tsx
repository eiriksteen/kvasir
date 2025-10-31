'use client';

import React, { useEffect } from 'react';
import { useState } from 'react';
import { BarChart3, Zap, Folder, Brain, Database } from 'lucide-react';
import { Dataset } from '@/types/data-objects';
import { DataSource } from '@/types/data-sources';
import { useAgentContext, useAnalyses, useDatasets, usePipelines, useProject, useDataSources } from '@/hooks';
import { useSession } from 'next-auth/react';
import { redirect } from 'next/navigation';
import { AnalysisSmall } from '@/types/analysis';
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
    openTab: (id: UUID | null, closable?: boolean) => void;
}

export default function EntitySidebar({ projectId, openTab }: EntitySidebarProps) {
    const [width, setWidth] = useState(260);
    const [isDragging, setIsDragging] = useState(false);
    const [showAddDataSourceToProject, setShowAddDataSourceToProject] = useState(false);
    const [showAddAnalysis, setShowAddAnalysis] = useState(false);
    const [showAddDatasetToProject, setShowAddDatasetToProject] = useState(false);
    const [showAddPipeline, setShowAddPipeline] = useState(false);
    const [showAddModelToProject, setShowAddModelToProject] = useState(false);
    
    const DEFAULT_WIDTH = 260;
    const MIN_WIDTH = 160;
    const COLLAPSE_THRESHOLD = 100;
    const COLLAPSED_WIDTH = 40;
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

    const { dataSources } = useDataSources(projectId);
    const { datasets } = useDatasets(projectId);
    const { pipelines } = usePipelines(projectId);
    const { modelEntities } = useModelEntities(projectId);
    const { analysisObjects } = useAnalyses(projectId);

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

    const toggleSection = (section: keyof typeof expandedSections) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    const handleDatasetToggle = (dataset: Dataset) => {
        const isActive = datasetsInContext.some((d: UUID) => d === dataset.id);
        if (isActive) {
            removeDatasetFromContext(dataset.id);
        } else {
            addDatasetToContext(dataset.id);
        }
    };

    const handleDataSourceToggle = (dataSource: DataSource) => {
        const isActive = dataSourcesInContext.some((ds: UUID) => ds === dataSource.id);
        if (isActive) {
            removeDataSourceFromContext(dataSource.id);
        } else {
            addDataSourceToContext(dataSource.id);
        }
    };

    const handleAnalysisToggle = (analysis: AnalysisSmall) => {
        const isActive = analysesInContext.some((a: UUID) => a === analysis.id);
        if (isActive) {
            removeAnalysisFromContext(analysis.id);
        } else {
            addAnalysisToContext(analysis.id);
        }
    };

    const handlePipelineToggle = (pipeline: Pipeline) => {

        const isActive = pipelinesInContext.some((p: UUID) => p === pipeline.id);
        if (isActive) {
            removePipelineFromContext(pipeline.id);
        } else {
            addPipelineToContext(pipeline.id);
        }
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

    const handleModelToggle = (model: ModelEntity) => {
        const isActive = modelEntitiesInContext.some((m: UUID) => m === model.id);
        if (isActive) {
            removeModelEntityFromContext(model.id);
        } else {
            addModelEntityToContext(model.id);
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
                    <div>
                        <div className="flex items-center justify-between pl-4 pr-3 h-9 border-b border-t border-gray-400 bg-gray-100 cursor-pointer hover:bg-gray-200 transition-colors" onClick={() => toggleSection('dataSources')}>
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
                                        isInContext={dataSourcesInContext.some((ds: UUID) => ds === dataSource.id)}
                                        onClick={() => handleDataSourceToggle(dataSource)}
                                        onOpenTab={() => openTab(dataSource.id, true)}
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

                    <div className="pl-4 h-9 border-b border-gray-400 bg-gray-100 cursor-pointer hover:bg-gray-200 transition-colors flex items-center" onClick={() => setShowEntities(!showEntities)}>
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
                                            isInContext={datasetsInContext.some((d: UUID) => d === dataset.id)}
                                            onClick={() => handleDatasetToggle(dataset)}
                                            onOpenTab={() => openTab(dataset.id, true)}
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
                                    <EntityItem 
                                        key={model.id} 
                                        item={model} 
                                        type="model_entity" 
                                        isInContext={modelEntitiesInContext.some((m: UUID) => m === model.id)} 
                                        onClick={() => handleModelToggle(model)}
                                        onOpenTab={() => openTab(model.id, true)}
                                    />
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
                            count={analysisObjects.length}
                            color="purple"
                            onToggle={() => toggleSection('analysis')}
                            onAdd={() => setShowAddAnalysis(true)}
                        />
                        {expandedSections.analysis && (
                            <div className="bg-[#004806]/10 border-l-2 border-[#004806]">
                                {analysisObjects.map((analysis) => (
                                    <EntityItem
                                        key={analysis.id}
                                        item={analysis}
                                        type="analysis"
                                        isInContext={analysesInContext.some((a: UUID) => a === analysis.id)}
                                        onClick={() => handleAnalysisToggle(analysis)}
                                        onOpenTab={() => openTab(analysis.id, true)}
                                    />
                                ))}
                                {analysisObjects.length === 0 && (
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
                                        isInContext={pipelinesInContext.some((p: UUID) => p === pipeline.id)}
                                        onClick={() => handlePipelineToggle(pipeline)}
                                        onOpenTab={() => openTab(pipeline.id, true)}
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
                        <div className="flex items-center justify-center h-9 border-b border-t border-gray-400 bg-gray-100">
                            <AddEntityButton type="data_source" size={14} onAdd={() => setShowAddDataSourceToProject(true)} />
                        </div>

                        {/* Centered entity buttons */}
                        <div className="flex-1 flex flex-col items-center justify-center gap-2">
                            <AddEntityButton type="dataset" size={14} onAdd={() => setShowAddDatasetToProject(true)} />
                            <AddEntityButton type="model_entity" size={14} onAdd={() => setShowAddModelToProject(true)} />
                            <AddEntityButton type="analysis" size={14} onAdd={() => setShowAddAnalysis(true)} />
                            <AddEntityButton type="pipeline" size={14} onAdd={() => setShowAddPipeline(true)} />
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