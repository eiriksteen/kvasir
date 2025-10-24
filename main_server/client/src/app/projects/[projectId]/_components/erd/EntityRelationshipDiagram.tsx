import React, { useCallback, useEffect, useMemo } from 'react';
import {
    ReactFlow,
    Node,
    // Controls,
    // MiniMap,
    EdgeTypes,
    MarkerType,
    Edge,
    useNodesState,
    useEdgesState,
    Handle,
    Position,
    useReactFlow,
    useOnViewportChange,
    Viewport
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useProject } from '@/hooks/useProject';
import { 
  ProjectDataSourceInDB, 
  ProjectDatasetInDB, 
  ProjectAnalysisInDB, 
  ProjectPipelineInDB, 
  ProjectModelEntityInDB 
} from '@/types/project';
import { ReactFlowProvider } from '@xyflow/react';
import DatasetBox from '@/app/projects/[projectId]/_components/erd/DatasetBox';
import AnalysisBox from '@/app/projects/[projectId]/_components/erd/AnalysisBox';
import TransportEdge from '@/app/projects/[projectId]/_components/erd/TransportEdge';
import DataSourceBox from '@/app/projects/[projectId]/_components/erd/DataSourceBox';
import PipelineBox from '@/app/projects/[projectId]/_components/erd/PipelineBox';
import { UUID } from 'crypto';
import ModelEntityBox from '@/app/projects/[projectId]/_components/erd/ModelEntityBox';
import { useProjectGraph } from '@/hooks/useProjectGraph';
import { computeBoxEdgeLocations } from '@/app/projects/[projectId]/_components/erd/computeBoxEdgeLocations';
import { useTabContext } from '@/hooks/useTabContext';

const DataSourceNodeWrapper = ({ data }: { data: { dataSourceId: UUID } }) => (
  <>
    <DataSourceBox
      dataSourceId={data.dataSourceId}
    />
    <Handle type="target" position={Position.Top} style={{ background: '#6b7280', left: 'calc(50% - 8px)' }} id="top-target" />
    <Handle type="source" position={Position.Top} style={{ background: '#6b7280', left: 'calc(50% + 8px)' }} id="top-source" />
    <Handle type="target" position={Position.Right} style={{ background: '#6b7280', top: 'calc(50% - 8px)' }} id="right-target" />
    <Handle type="source" position={Position.Right} style={{ background: '#6b7280', top: 'calc(50% + 8px)' }} id="right-source" />
    <Handle type="target" position={Position.Bottom} style={{ background: '#6b7280', left: 'calc(50% + 8px)' }} id="bottom-target" />
    <Handle type="source" position={Position.Bottom} style={{ background: '#6b7280', left: 'calc(50% - 8px)' }} id="bottom-source" />
    <Handle type="target" position={Position.Left} style={{ background: '#6b7280', top: 'calc(50% + 8px)' }} id="left-target" />
    <Handle type="source" position={Position.Left} style={{ background: '#6b7280', top: 'calc(50% - 8px)' }} id="left-source" />
  </>
);

// Wrapper component to adapt ReactFlow node props to Dataset component props
const DatasetNodeWrapper = ({ data }: { data: { datasetId: UUID; projectId: UUID } }) => (
  <>
    <DatasetBox
      datasetId={data.datasetId}
      projectId={data.projectId}
    />
    <Handle type="target" position={Position.Top} style={{ background: '#0E4F70', left: 'calc(50% - 8px)' }} id="top-target" />
    <Handle type="source" position={Position.Top} style={{ background: '#0E4F70', left: 'calc(50% + 8px)' }} id="top-source" />
    <Handle type="target" position={Position.Right} style={{ background: '#0E4F70', top: 'calc(50% - 8px)' }} id="right-target" />
    <Handle type="source" position={Position.Right} style={{ background: '#0E4F70', top: 'calc(50% + 8px)' }} id="right-source" />
    <Handle type="target" position={Position.Bottom} style={{ background: '#0E4F70', left: 'calc(50% + 8px)' }} id="bottom-target" />
    <Handle type="source" position={Position.Bottom} style={{ background: '#0E4F70', left: 'calc(50% - 8px)' }} id="bottom-source" />
    <Handle type="target" position={Position.Left} style={{ background: '#0E4F70', top: 'calc(50% + 8px)' }} id="left-target" />
    <Handle type="source" position={Position.Left} style={{ background: '#0E4F70', top: 'calc(50% - 8px)' }} id="left-source" />
  </>
);

// Wrapper component to adapt ReactFlow node props to Analysis component props
const AnalysisNodeWrapper = ({ data }: { data: { analysisId: UUID; projectId: UUID } }) => (
  <>
  <AnalysisBox
    analysisId={data.analysisId}
    projectId={data.projectId}
  />
  <Handle type="target" position={Position.Top} style={{ background: '#004806', left: 'calc(50% - 8px)' }} id="top-target" />
  <Handle type="source" position={Position.Top} style={{ background: '#004806', left: 'calc(50% + 8px)' }} id="top-source" />
  <Handle type="target" position={Position.Right} style={{ background: '#004806', top: 'calc(50% - 8px)' }} id="right-target" />
  <Handle type="source" position={Position.Right} style={{ background: '#004806', top: 'calc(50% + 8px)' }} id="right-source" />
  <Handle type="target" position={Position.Bottom} style={{ background: '#004806', left: 'calc(50% + 8px)' }} id="bottom-target" />
  <Handle type="source" position={Position.Bottom} style={{ background: '#004806', left: 'calc(50% - 8px)' }} id="bottom-source" />
  <Handle type="target" position={Position.Left} style={{ background: '#004806', top: 'calc(50% + 8px)' }} id="left-target" />
  <Handle type="source" position={Position.Left} style={{ background: '#004806', top: 'calc(50% - 8px)' }} id="left-source" />
  </>
);

const PipelineNodeWrapper = ({ data }: { data: { pipelineId: UUID; projectId: UUID } }) => (
  <>
    <PipelineBox
      pipelineId={data.pipelineId}
      projectId={data.projectId}
    />
    <Handle type="target" position={Position.Top} style={{ background: '#840B08', left: 'calc(50% - 8px)' }} id="top-target" />
    <Handle type="source" position={Position.Top} style={{ background: '#840B08', left: 'calc(50% + 8px)' }} id="top-source" />
    <Handle type="target" position={Position.Right} style={{ background: '#840B08', top: 'calc(50% - 8px)' }} id="right-target" />
    <Handle type="source" position={Position.Right} style={{ background: '#840B08', top: 'calc(50% + 8px)' }} id="right-source" />
    <Handle type="target" position={Position.Bottom} style={{ background: '#840B08', left: 'calc(50% + 8px)' }} id="bottom-target" />
    <Handle type="source" position={Position.Bottom} style={{ background: '#840B08', left: 'calc(50% - 8px)' }} id="bottom-source" />
    <Handle type="target" position={Position.Left} style={{ background: '#840B08', top: 'calc(50% + 8px)' }} id="left-target" />
    <Handle type="source" position={Position.Left} style={{ background: '#840B08', top: 'calc(50% - 8px)' }} id="left-source" />
  </>
);

const ModelEntityNodeWrapper = ({ data }: { data: { modelEntityId: UUID; projectId: UUID } }) => (
  <>
    <ModelEntityBox
      modelEntityId={data.modelEntityId}
      projectId={data.projectId}
    />
    <Handle type="target" position={Position.Top} style={{ background: '#491A32', left: 'calc(50% - 8px)' }} id="top-target" />
    <Handle type="source" position={Position.Top} style={{ background: '#491A32', left: 'calc(50% + 8px)' }} id="top-source" />
    <Handle type="target" position={Position.Right} style={{ background: '#491A32', top: 'calc(50% - 8px)' }} id="right-target" />
    <Handle type="source" position={Position.Right} style={{ background: '#491A32', top: 'calc(50% + 8px)' }} id="right-source" />
    <Handle type="target" position={Position.Bottom} style={{ background: '#491A32', left: 'calc(50% + 8px)' }} id="bottom-target" />
    <Handle type="source" position={Position.Bottom} style={{ background: '#491A32', left: 'calc(50% - 8px)' }} id="bottom-source" />
    <Handle type="target" position={Position.Left} style={{ background: '#491A32', top: 'calc(50% + 8px)' }} id="left-target" />
    <Handle type="source" position={Position.Left} style={{ background: '#491A32', top: 'calc(50% - 8px)' }} id="left-source" />
  </>
);

const nodeTypes = {
  dataset: DatasetNodeWrapper,
  analysis: AnalysisNodeWrapper,
  dataSource: DataSourceNodeWrapper,
  pipeline: PipelineNodeWrapper,
  modelEntity: ModelEntityNodeWrapper,
};

const edgeTypes: EdgeTypes = {
  'custom-edge': TransportEdge,
};

interface EntityRelationshipDiagramProps {
  projectId: UUID;
}

function EntityRelationshipDiagramContent({ projectId }: EntityRelationshipDiagramProps) {

  const getEdgeColor = useCallback((sourceType: string): string => {
    switch (sourceType) {
      case 'dataSource':
        return '#6b7280'; // Gray - unchanged
      case 'dataset':
        return '#0E4F70'; // Dataset color
      case 'analysis':
        return '#004806'; // Analysis color
      case 'pipeline':
        return '#840B08'; // Pipeline color
      case 'modelEntity':
        return '#491A32'; // Model entity color
      default:
        return '#0E4F70'; // Default dataset color
    }
  }, []);

  const { project, updatePosition, updateProjectViewPort } = useProject(projectId);
  const { projectGraph } = useProjectGraph(projectId);
  const { openTab } = useTabContext(projectId);
  
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const { setViewport } = useReactFlow();


  useOnViewportChange({
    onEnd: (viewport: Viewport) => updateProjectViewPort({x: viewport.x, y: viewport.y, zoom: viewport.zoom})
    }
  );

  useEffect(() => {
    if (project) {
      setViewport({
        x: project.viewPortX,
        y: project.viewPortY,
        zoom: project.viewPortZoom,
      });
    }
  }, [project, setViewport]);

  // Handler to open tabs when node is clicked
  const handleNodeClick = useCallback(
    (event: React.MouseEvent, node: Node) => {
      if (!node || !node.id) return;
      openTab(node.id as UUID, true);
    },
    [openTab]
  );

  // Handler to open tabs when node is selected
  // Kinda ugly but it's needed to prevent needing to double click the first tab we open
  const handleSelectionChange = useCallback(
    ({ nodes }: { nodes: Node[] }) => {
      if (nodes.length > 0) {
        const selectedNode = nodes[0];
        openTab(selectedNode.id as UUID, true);
      }
    },
    [openTab]
  );

  // Memoize nodes
  const memoizedNodes = useMemo(() => {
    if (!project) {
      return [];
    }

    const nodes: Node[] = [];

    // Add data source nodes
    project.dataSources.forEach((projectDataSource: ProjectDataSourceInDB) => {
      nodes.push({
        id: projectDataSource.dataSourceId,
        type: 'dataSource',
        position: { x: projectDataSource.xPosition, y: projectDataSource.yPosition },
        data: {
          dataSourceId: projectDataSource.dataSourceId,
        },
      });
    });

    // Add dataset nodes
    project.datasets.forEach((projectDataset: ProjectDatasetInDB) => {
      nodes.push({
        id: projectDataset.datasetId,
        type: 'dataset',
        position: { x: projectDataset.xPosition, y: projectDataset.yPosition },
        data: {
          datasetId: projectDataset.datasetId,
          projectId: projectId,
        },
      });
    });

    // Add pipeline nodes
    project.pipelines.forEach((projectPipeline: ProjectPipelineInDB) => {
      nodes.push({
        id: projectPipeline.pipelineId,
        type: 'pipeline',
        position: { x: projectPipeline.xPosition, y: projectPipeline.yPosition },
        data: {
          pipelineId: projectPipeline.pipelineId,
          projectId: projectId,
        },
      });
    });

    // Add analysis nodes
    project.analyses.forEach((projectAnalysis: ProjectAnalysisInDB) => {
      nodes.push({
        id: projectAnalysis.analysisId,
        type: 'analysis',
        position: { x: projectAnalysis.xPosition, y: projectAnalysis.yPosition },
        data: {
          analysisId: projectAnalysis.analysisId,
          projectId: projectId,
        },
      });
    });

    // Add model entity nodes
    project.modelEntities.forEach((projectModelEntity: ProjectModelEntityInDB) => {
      nodes.push({
        id: projectModelEntity.modelEntityId,
        type: 'modelEntity',
        position: { x: projectModelEntity.xPosition, y: projectModelEntity.yPosition },
        data: {
          modelEntityId: projectModelEntity.modelEntityId,
          projectId: projectId,
        },
      });
    });

    return nodes;

  }, [project, projectId]);

  // Memoize edges - uses current node positions from state for live updates during dragging
  const memoizedEdges = useMemo(() => {
    if (!projectGraph || nodes.length === 0) {
      return [];
    }

    // Helper to get entity position from current nodes state (updates during dragging)
    const getEntityPosition = (entityId: UUID): { xPosition: number, yPosition: number } | null => {
      const currentNode = nodes.find(n => n.id === entityId);
      if (currentNode) {
        return { xPosition: currentNode.position.x, yPosition: currentNode.position.y };
      }
      return null;
    };

    // Generic edge creation helper
    const createEdge = (
      sourceId: UUID,
      targetId: UUID,
      sourceType: 'dataSource' | 'dataset' | 'analysis' | 'pipeline' | 'modelEntity'
    ): Edge | null => {
      const sourcePos = getEntityPosition(sourceId);
      const targetPos = getEntityPosition(targetId);
      if (!sourcePos || !targetPos) return null;

      const edgeLocation = computeBoxEdgeLocations(sourcePos, targetPos);
      return {
        id: String(`${sourceId}->${targetId}`),
        source: sourceId,
        target: targetId,
        type: 'default',
        animated: true,
        style: { stroke: getEdgeColor(sourceType), strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed },
        sourceHandle: edgeLocation.from,
        targetHandle: edgeLocation.to,
      } as Edge;
    };

    // Helper to process all connections for an entity
    const processEntityConnections = (
      entityId: UUID,
      connections: {
        fromDataSources?: UUID[];
        fromDatasets?: UUID[];
        fromAnalyses?: UUID[];
        fromPipelines?: UUID[];
        fromModelEntities?: UUID[];
        toDataSources?: UUID[];
        toDatasets?: UUID[];
        toAnalyses?: UUID[];
        toPipelines?: UUID[];
        toModelEntities?: UUID[];
      },
      entityType: 'dataSource' | 'dataset' | 'analysis' | 'pipeline' | 'modelEntity'
    ): Edge[] => {
      const edges: Edge[] = [];

      // Process all outgoing connections (to* fields)
      const outgoingConnections = [
        { targets: connections.toDataSources || [], type: entityType },
        { targets: connections.toDatasets || [], type: entityType },
        { targets: connections.toAnalyses || [], type: entityType },
        { targets: connections.toPipelines || [], type: entityType },
        { targets: connections.toModelEntities || [], type: entityType },
      ];

      outgoingConnections.forEach(({ targets, type }) => {
        targets.forEach(targetId => {
          const edge = createEdge(entityId, targetId, type);
          if (edge) edges.push(edge);
        });
      });

      return edges;
    };

    // Generate all edges from all entity types
    const allEdges: Edge[] = [
      ...projectGraph.dataSources.flatMap(ds => processEntityConnections(ds.id, ds.connections, 'dataSource')),
      ...projectGraph.datasets.flatMap(d => processEntityConnections(d.id, d.connections, 'dataset')),
      ...projectGraph.analyses.flatMap(a => processEntityConnections(a.id, a.connections, 'analysis')),
      ...projectGraph.pipelines.flatMap(p => processEntityConnections(p.id, p.connections, 'pipeline')),
      ...projectGraph.modelEntities.flatMap(m => processEntityConnections(m.id, m.connections, 'modelEntity')),
    ];

    return allEdges;
  }, [projectGraph, getEdgeColor, nodes]);

  // Sync nodes: only update if the set of node IDs has changed
  useEffect(() => {
    const currentNodeIds = nodes.map(n => n.id).sort().join(',');
    const newNodeIds = memoizedNodes.map(n => n.id).sort().join(',');
    
    if (currentNodeIds !== newNodeIds) {
      setNodes(memoizedNodes);
    }
  }, [memoizedNodes, nodes, setNodes]);

  // Sync edges: always update when memoized edges change (they now include live positions)
  useEffect(() => {
    setEdges(memoizedEdges);
  }, [memoizedEdges, setEdges]);

  const handleNodeDragStop = useCallback((event: React.MouseEvent, node: Node) => {
    if (!project || !node || !node.id) return;

    // Determine entity type by checking which list contains the node ID
    let entityType: "data_source" | "dataset" | "analysis" | "pipeline" | "model_entity" | null = null;

    if (project.dataSources.some(ds => ds.dataSourceId === node.id)) {
      entityType = "data_source";
    } else if (project.datasets.some(ds => ds.datasetId === node.id)) {
      entityType = "dataset";
    } else if (project.analyses.some(a => a.analysisId === node.id)) {
      entityType = "analysis";
    } else if (project.pipelines.some(p => p.pipelineId === node.id)) {
      entityType = "pipeline";
    } else if (project.modelEntities.some(me => me.modelEntityId === node.id)) {
      entityType = "model_entity";
    }

    if (entityType) {
      updatePosition({
        entityType,
        entityId: node.id as UUID,
        xPosition: node.position.x,
        yPosition: node.position.y,
      });
    }
  }, [project, updatePosition]);

  return (
    <div className="w-full h-full bg-white">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        // fitView
        onNodeDragStop={handleNodeDragStop}
        onNodeClick={handleNodeClick}
        onSelectionChange={handleSelectionChange}
        className="reactflow-no-watermark"
      >
        {/* <Controls /> */}
        {/* <MiniMap 
          style={{
            background: '#0a101c',
            border: '1px solid #1d2d50'
          }}
          nodeColor="#3b82f6"
          maskColor="rgba(0, 0, 0, 0.1)"
        /> */}
      </ReactFlow>
    </div>
  );
};

export default function EntityRelationshipDiagram({ projectId }: EntityRelationshipDiagramProps) {
  return (
    <ReactFlowProvider>
      <EntityRelationshipDiagramContent projectId={projectId} />
    </ReactFlowProvider>
  );
}