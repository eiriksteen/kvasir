'use client';

import React, { useState } from 'react';
import { BarChart3, Zap, Folder, Brain, Database } from 'lucide-react';
import { Dataset } from '@/types/ontology/dataset';
import { DataSource } from '@/types/ontology/data-source';
import { Analysis } from '@/types/ontology/analysis';
import EntityItem from '@/app/projects/[projectId]/_components/entity-sidebar/EntityItem';
import AddEntityButton from '@/app/projects/[projectId]/_components/entity-sidebar/AddEntityButton';
import EntityOverviewItem from '@/app/projects/[projectId]/_components/entity-sidebar/EntityOverviewItem';
import { UUID } from 'crypto';
import { Pipeline } from '@/types/ontology/pipeline';
import { ModelInstantiated } from '@/types/ontology/model';
import { useAgentContext } from '@/hooks/useAgentContext';
import { useOntology } from '@/hooks/useOntology';

interface EntityTreeProps {
    projectId: UUID;
    openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void;
}

export default function EntityTree({ projectId, openTab }: EntityTreeProps) {
    const [expandedSections, setExpandedSections] = useState({
        dataSources: false,
        datasets: false,
        analysis: false,
        pipelines: false,
        models: false
    });
    const [showEntities, setShowEntities] = useState(true);

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
        modelsInstantiatedInContext,
        addModelEntityToContext,
        removeModelEntityFromContext,
    } = useAgentContext(projectId);

    const { dataSources, datasets, pipelines, modelsInstantiated, analyses } = useOntology(projectId);

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

    const handleAnalysisToggle = (analysis: Analysis) => {
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

    const handleModelToggle = (model: ModelInstantiated) => {
        const isActive = modelsInstantiatedInContext.some((m: UUID) => m === model.id);
        if (isActive) {
            removeModelEntityFromContext(model.id);
        } else {
            addModelEntityToContext(model.id);
        }
    };

    console.log(dataSources);
    

    return (
        <>
            {/* Data Sources Section */}
            <div>
                <div className="flex items-center justify-between pl-4 pr-3 h-7 border-b border-t border-gray-400 bg-gray-100 cursor-pointer hover:bg-gray-200 transition-colors" onClick={() => toggleSection('dataSources')}>
                    <h3 className='text-xs font-mono uppercase tracking-wider text-gray-900'> DATA SOURCES </h3>
                    <div onClick={(e) => e.stopPropagation()}>
                        <AddEntityButton type="data_source" size={11} projectId={projectId} />
                    </div>
                </div>
                {expandedSections.dataSources && (
                    <div className="bg-gray-50 border-l-2 border-gray-600">
                        {dataSources && dataSources.length > 0 ? (
                            dataSources.map((dataSource) => (
                                <EntityItem
                                    key={dataSource.id}
                                    item={dataSource}
                                    type="data_source"
                                    isInContext={dataSourcesInContext.some((ds: UUID) => ds === dataSource.id)}
                                    onClick={() => handleDataSourceToggle(dataSource)}
                                    onOpenTab={() => openTab(dataSource.id, true)}
                                />
                            ))
                        ) : (
                            <div className="px-3 py-4 text-center">
                                <Database size={16} className="text-gray-400 mx-auto mb-2" />
                                <p className="text-xs text-gray-500">No data sources</p>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Entities Header */}
            <div className="pl-4 h-7 border-b border-gray-400 bg-gray-100 cursor-pointer hover:bg-gray-200 transition-colors flex items-center" onClick={() => setShowEntities(!showEntities)}>
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
                            projectId={projectId}
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
                            count={modelsInstantiated?.length || 0}
                            color="emerald"
                            onToggle={() => toggleSection('models')}
                            projectId={projectId}
                        />
                        {modelsInstantiated && expandedSections.models && (
                            <div className="bg-[#491A32]/10 border-l-2 border-[#491A32]">
                                {modelsInstantiated.map((model) => (
                                    <EntityItem 
                                        key={model.id} 
                                        item={model} 
                                        type="model_instantiated" 
                                        isInContext={modelsInstantiatedInContext.some((m: UUID) => m === model.id)} 
                                        onClick={() => handleModelToggle(model)}
                                        onOpenTab={() => openTab(model.id, true)}
                                    />
                                ))}
                                {modelsInstantiated.length === 0 && (
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
                            count={analyses?.length || 0}
                            color="purple"
                            onToggle={() => toggleSection('analysis')}
                            projectId={projectId}
                        />
                        {expandedSections.analysis && (
                            <div className="bg-[#004806]/10 border-l-2 border-[#004806]">
                                {analyses?.map((analysis) => (
                                    <EntityItem
                                        key={analysis.id}
                                        item={analysis}
                                        type="analysis"
                                        isInContext={analysesInContext.some((a: UUID) => a === analysis.id)}
                                        onClick={() => handleAnalysisToggle(analysis)}
                                        onOpenTab={() => openTab(analysis.id, true)}
                                    />
                                ))}
                                {analyses?.length === 0 && (
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
                            projectId={projectId}
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
        </>
    );
}
