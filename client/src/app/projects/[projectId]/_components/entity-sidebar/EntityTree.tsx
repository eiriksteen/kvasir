'use client';

import React, { useState, useEffect, useRef } from 'react';
import { BarChart3, Zap, Folder, Brain, Database, ChevronRight, ChevronDown, FolderOpen, Trash2 } from 'lucide-react';
import EntityItem from '@/app/projects/[projectId]/_components/entity-sidebar/EntityItem';
import AddEntityButton from '@/app/projects/[projectId]/_components/entity-sidebar/AddEntityButton';
import EntityOverviewItem from '@/app/projects/[projectId]/_components/entity-sidebar/EntityOverviewItem';
import ConfirmDialog from '@/components/ConfirmDialog';
import { UUID } from 'crypto';
import { useAgentContext } from '@/hooks/useAgentContext';
import { useEntityGraph } from '@/hooks/useEntityGraph';
import { useOntology } from '@/hooks/useOntology';
import { GraphNode, LeafNode, BranchNode } from '@/types/ontology/entity-graph';

interface EntityTreeProps {
    projectId: UUID;
    openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void;
}

function countLeafNodes(nodes: GraphNode[]): number {
    let count = 0;
    for (const node of nodes) {
        if (node.nodeType === 'leaf') {
            count += 1;
        } else if (node.nodeType === 'branch') {
            count += countLeafNodes(node.children);
        }
    }
    return count;
}

interface TreeNodeProps {
    node: GraphNode;
    entityType: 'dataset' | 'analysis' | 'pipeline' | 'model_instantiated' | 'data_source';
    isInContext: (entityId: UUID) => boolean;
    onToggle: (entityId: UUID) => void;
    onOpenTab: (entityId: UUID) => void;
    expandedBranches: Set<UUID>;
    onToggleBranch: (branchId: UUID) => void;
    onContextMenu: (e: React.MouseEvent, nodeId: UUID) => void;
    depth?: number;
}

function TreeNode({ node, entityType, isInContext, onToggle, onOpenTab, expandedBranches, onToggleBranch, onContextMenu, depth = 0 }: TreeNodeProps) {
    if (node.nodeType === 'leaf') {
        const leafNode = node as LeafNode;
        if (leafNode.entityType === 'pipeline_run') {
            return null;
        }
        
        return (
            <div
                onContextMenu={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onContextMenu(e, leafNode.id);
                }}
            >
                <EntityItem
                    key={leafNode.id}
                    item={leafNode}
                    isInContext={isInContext(leafNode.entityId)}
                    onClick={() => onToggle(leafNode.entityId)}
                    onOpenTab={() => onOpenTab(leafNode.entityId)}
                />
            </div>
        );
    }

    const branchNode = node as BranchNode;
    const isExpanded = expandedBranches.has(branchNode.id);
    const indentStyle = { paddingLeft: `${depth * 12 + 12}px` };

    return (
        <div key={branchNode.id}>
            <div
                className="flex items-center gap-1 px-3 py-1 text-sm cursor-pointer hover:bg-gray-200/50 transition-colors"
                style={indentStyle}
                onClick={(e) => {
                    e.stopPropagation();
                    onToggleBranch(branchNode.id);
                }}
                onContextMenu={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onContextMenu(e, branchNode.id);
                }}
            >
                {isExpanded ? (
                    <ChevronDown size={12} className="text-gray-500 flex-shrink-0" />
                ) : (
                    <ChevronRight size={12} className="text-gray-500 flex-shrink-0" />
                )}
                {isExpanded ? (
                    <FolderOpen size={12} className="text-gray-600 flex-shrink-0" />
                ) : (
                    <Folder size={12} className="text-gray-600 flex-shrink-0" />
                )}
                <span className="truncate text-gray-700 font-mono text-xs">{branchNode.name}</span>
            </div>
            {isExpanded && branchNode.children && (
                <div>
                    {branchNode.children.map((child) => (
                        <TreeNode
                            key={child.id}
                            node={child}
                            entityType={entityType}
                            isInContext={isInContext}
                            onToggle={onToggle}
                            onOpenTab={onOpenTab}
                            expandedBranches={expandedBranches}
                            onToggleBranch={onToggleBranch}
                            onContextMenu={onContextMenu}
                            depth={depth + 1}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}

export default function EntityTree({ projectId, openTab }: EntityTreeProps) {
    const [expandedSections, setExpandedSections] = useState({
        dataSources: false,
        datasets: false,
        analysis: false,
        pipelines: false,
        models: false
    });
    const [expandedBranches, setExpandedBranches] = useState<Set<UUID>>(new Set());
    const [showEntities, setShowEntities] = useState(true);
    const [contextMenu, setContextMenu] = useState<{ x: number; y: number; nodeId: UUID } | null>(null);
    const [showConfirmDialog, setShowConfirmDialog] = useState(false);
    const [nodeToDelete, setNodeToDelete] = useState<UUID | null>(null);
    const contextMenuRef = useRef<HTMLDivElement>(null);

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

    const { entityGraph } = useEntityGraph(projectId);
    const { deleteEntityBranch } = useOntology(projectId);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (contextMenuRef.current && !contextMenuRef.current.contains(event.target as Node)) {
                setContextMenu(null);
            }
        };

        if (contextMenu) {
            document.addEventListener('click', handleClickOutside);
            return () => {
                document.removeEventListener('click', handleClickOutside);
            };
        }
    }, [contextMenu]);

    const toggleSection = (section: keyof typeof expandedSections) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    const toggleBranch = (branchId: UUID) => {
        setExpandedBranches(prev => {
            const next = new Set(prev);
            if (next.has(branchId)) {
                next.delete(branchId);
            } else {
                next.add(branchId);
            }
            return next;
        });
    };

    const handleDatasetToggle = (entityId: UUID) => {
        const isActive = datasetsInContext.some((d: UUID) => d === entityId);
        if (isActive) {
            removeDatasetFromContext(entityId);
        } else {
            addDatasetToContext(entityId);
        }
    };

    const handleDataSourceToggle = (entityId: UUID) => {
        const isActive = dataSourcesInContext.some((ds: UUID) => ds === entityId);
        if (isActive) {
            removeDataSourceFromContext(entityId);
        } else {
            addDataSourceToContext(entityId);
        }
    };

    const handleAnalysisToggle = (entityId: UUID) => {
        const isActive = analysesInContext.some((a: UUID) => a === entityId);
        if (isActive) {
            removeAnalysisFromContext(entityId);
        } else {
            addAnalysisToContext(entityId);
        }
    };

    const handlePipelineToggle = (entityId: UUID) => {
        const isActive = pipelinesInContext.some((p: UUID) => p === entityId);
        if (isActive) {
            removePipelineFromContext(entityId);
        } else {
            addPipelineToContext(entityId);
        }
    };

    const handleModelToggle = (entityId: UUID) => {
        const isActive = modelsInstantiatedInContext.some((m: UUID) => m === entityId);
        if (isActive) {
            removeModelEntityFromContext(entityId);
        } else {
            addModelEntityToContext(entityId);
        }
    };

    const handleContextMenu = (e: React.MouseEvent, nodeId: UUID) => {
        e.preventDefault();
        setContextMenu({
            x: e.clientX,
            y: e.clientY,
            nodeId
        });
    };

    const handleDeleteClick = () => {
        if (!contextMenu) return;
        setNodeToDelete(contextMenu.nodeId);
        setContextMenu(null);
        setShowConfirmDialog(true);
    };

    const handleConfirmDelete = async () => {
        if (!nodeToDelete) return;
        
        try {
            await deleteEntityBranch({ nodeId: nodeToDelete });
            setShowConfirmDialog(false);
            setNodeToDelete(null);
        } catch (error) {
            console.error('Failed to delete entity branch:', error);
            setShowConfirmDialog(false);
            setNodeToDelete(null);
        }
    };

    const handleCancelDelete = () => {
        setShowConfirmDialog(false);
        setNodeToDelete(null);
    };

    return (
        <>
            {contextMenu && (
                <div
                    ref={contextMenuRef}
                    className="fixed bg-white border border-gray-200 rounded z-50 shadow-sm"
                    style={{
                        left: `${contextMenu.x}px`,
                        top: `${contextMenu.y}px`
                    }}
                >
                    <button
                        onClick={handleDeleteClick}
                        className="w-full px-3 py-1.5 text-left text-xs font-mono text-gray-700 hover:bg-gray-100 flex items-center gap-2 transition-colors"
                    >
                        <Trash2 size={12} className="text-gray-500" />
                        Delete
                    </button>
                </div>
            )}
            <ConfirmDialog
                isOpen={showConfirmDialog}
                title="Delete Item"
                message="Are you sure you want to delete this item? This action cannot be undone."
                confirmText="Delete"
                cancelText="Cancel"
                onConfirm={handleConfirmDelete}
                onCancel={handleCancelDelete}
            />
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
                        {entityGraph?.dataSources && entityGraph.dataSources.length > 0 ? (
                            entityGraph.dataSources.map((node) => (
                                <TreeNode
                                    key={node.id}
                                    node={node}
                                    entityType="data_source"
                                    isInContext={(id) => dataSourcesInContext.some((ds: UUID) => ds === id)}
                                    onToggle={handleDataSourceToggle}
                                    onOpenTab={(id) => openTab(id, true)}
                                    expandedBranches={expandedBranches}
                                    onToggleBranch={toggleBranch}
                                    onContextMenu={handleContextMenu}
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
                            count={entityGraph ? countLeafNodes(entityGraph.datasets) : 0}
                            color="blue"
                            onToggle={() => toggleSection('datasets')}
                            projectId={projectId}
                        />
                        {entityGraph?.datasets && expandedSections.datasets && (
                            <div className="bg-[#0E4F70]/10 border-l-2 border-[#0E4F70]">
                                {entityGraph.datasets.length > 0 ? (
                                    entityGraph.datasets.map((node) => (
                                        <TreeNode
                                            key={node.id}
                                            node={node}
                                            entityType="dataset"
                                            isInContext={(id) => datasetsInContext.some((d: UUID) => d === id)}
                                            onToggle={handleDatasetToggle}
                                            onOpenTab={(id) => openTab(id, true)}
                                            expandedBranches={expandedBranches}
                                            onToggleBranch={toggleBranch}
                                            onContextMenu={handleContextMenu}
                                        />
                                    ))
                                ) : (
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
                            count={entityGraph ? countLeafNodes(entityGraph.modelsInstantiated) : 0}
                            color="emerald"
                            onToggle={() => toggleSection('models')}
                            projectId={projectId}
                        />
                        {entityGraph?.modelsInstantiated && expandedSections.models && (
                            <div className="bg-[#491A32]/10 border-l-2 border-[#491A32]">
                                {entityGraph.modelsInstantiated.length > 0 ? (
                                    entityGraph.modelsInstantiated.map((node) => (
                                        <TreeNode
                                            key={node.id}
                                            node={node}
                                            entityType="model_instantiated"
                                            isInContext={(id) => modelsInstantiatedInContext.some((m: UUID) => m === id)}
                                            onToggle={handleModelToggle}
                                            onOpenTab={(id) => openTab(id, true)}
                                            expandedBranches={expandedBranches}
                                            onToggleBranch={toggleBranch}
                                            onContextMenu={handleContextMenu}
                                        />
                                    ))
                                ) : (
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
                            count={entityGraph ? countLeafNodes(entityGraph.analyses) : 0}
                            color="purple"
                            onToggle={() => toggleSection('analysis')}
                            projectId={projectId}
                        />
                        {entityGraph?.analyses && expandedSections.analysis && (
                            <div className="bg-[#004806]/10 border-l-2 border-[#004806]">
                                {entityGraph.analyses.length > 0 ? (
                                    entityGraph.analyses.map((node) => (
                                        <TreeNode
                                            key={node.id}
                                            node={node}
                                            entityType="analysis"
                                            isInContext={(id) => analysesInContext.some((a: UUID) => a === id)}
                                            onToggle={handleAnalysisToggle}
                                            onOpenTab={(id) => openTab(id, true)}
                                            expandedBranches={expandedBranches}
                                            onToggleBranch={toggleBranch}
                                            onContextMenu={handleContextMenu}
                                        />
                                    ))
                                ) : (
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
                            count={entityGraph ? countLeafNodes(entityGraph.pipelines) : 0}
                            color="orange"
                            onToggle={() => toggleSection('pipelines')}
                            projectId={projectId}
                        />
                        {entityGraph?.pipelines && expandedSections.pipelines && (
                            <div className="bg-[#840B08]/10 border-l-2 border-[#840B08]">
                                {entityGraph.pipelines.length > 0 ? (
                                    entityGraph.pipelines.map((node) => (
                                        <TreeNode
                                            key={node.id}
                                            node={node}
                                            entityType="pipeline"
                                            isInContext={(id) => pipelinesInContext.some((p: UUID) => p === id)}
                                            onToggle={handlePipelineToggle}
                                            onOpenTab={(id) => openTab(id, true)}
                                            expandedBranches={expandedBranches}
                                            onToggleBranch={toggleBranch}
                                            onContextMenu={handleContextMenu}
                                        />
                                    ))
                                ) : (
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
