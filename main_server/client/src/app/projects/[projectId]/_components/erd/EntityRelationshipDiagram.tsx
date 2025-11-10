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
import { ReactFlowProvider } from '@xyflow/react';
import DatasetBox from '@/app/projects/[projectId]/_components/erd/DatasetBox';
import AnalysisBox from '@/app/projects/[projectId]/_components/erd/AnalysisBox';
import TransportEdge from '@/app/projects/[projectId]/_components/erd/TransportEdge';
import DataSourceBox from '@/app/projects/[projectId]/_components/erd/DataSourceBox';
import PipelineBox from '@/app/projects/[projectId]/_components/erd/PipelineBox';
import { UUID } from 'crypto';
import ModelEntityBox from '@/app/projects/[projectId]/_components/erd/ModelEntityBox';
import { computeBoxEdgeLocations } from '@/app/projects/[projectId]/_components/erd/computeBoxEdgeLocations';

const DataSourceNodeWrapper = ({ data }: { data: { dataSourceId: UUID; projectId: UUID; openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void } }) => (
  <>
    <DataSourceBox
      dataSourceId={data.dataSourceId}
      projectId={data.projectId}
      openTab={data.openTab}
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
const DatasetNodeWrapper = ({ data }: { data: { datasetId: UUID; projectId: UUID; openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void } }) => (
  <>
    <DatasetBox
      datasetId={data.datasetId}
      projectId={data.projectId}
      openTab={data.openTab}
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
const AnalysisNodeWrapper = ({ data }: { data: { analysisId: UUID; projectId: UUID; openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void } }) => (
  <>
  <AnalysisBox
    analysisId={data.analysisId}
    projectId={data.projectId}
    openTab={data.openTab}
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

const PipelineNodeWrapper = ({ data }: { data: { pipelineId: UUID; projectId: UUID; openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void } }) => (
  <>
    <PipelineBox
      pipelineId={data.pipelineId}
      projectId={data.projectId}
      openTab={data.openTab}
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

const ModelEntityNodeWrapper = ({ data }: { data: { modelEntityId: UUID; projectId: UUID; openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void } }) => (
  <>
    <ModelEntityBox
      modelEntityId={data.modelEntityId}
      projectId={data.projectId}
      openTab={data.openTab}
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
  openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void;
}

function EntityRelationshipDiagramContent({ projectId, openTab }: EntityRelationshipDiagramProps) {

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


  // Memoize nodes
  const memoizedNodes = useMemo(() => {
    if (!project?.graph || !project?.projectNodes) {
      return [];
    }

    const nodes: Node[] = [];

    // Add data source nodes
    project.graph.dataSources.forEach((ds) => {
      const position = project.projectNodes.projectDataSources.find(p => p.dataSourceId === ds.id);
      if (position) {
        nodes.push({
          id: ds.id,
          type: 'dataSource',
          position: { x: position.xPosition, y: position.yPosition },
          data: {
            dataSourceId: ds.id,
            projectId: projectId,
            openTab,
          },
        });
      }
    });

    // Add dataset nodes
    project.graph.datasets.forEach((d) => {
      const position = project.projectNodes.projectDatasets.find(p => p.datasetId === d.id);
      if (position) {
        nodes.push({
          id: d.id,
          type: 'dataset',
          position: { x: position.xPosition, y: position.yPosition },
          data: {
            datasetId: d.id,
            projectId: projectId,
            openTab,
          },
        });
      }
    });

    // Add pipeline nodes
    project.graph.pipelines.forEach((p) => {
      const position = project.projectNodes.projectPipelines.find(pos => pos.pipelineId === p.id);
      if (position) {
        nodes.push({
          id: p.id,
          type: 'pipeline',
          position: { x: position.xPosition, y: position.yPosition },
          data: {
            pipelineId: p.id,
            projectId: projectId,
            openTab,
          },
        });
      }
    });

    // Add analysis nodes
    project.graph.analyses.forEach((a) => {
      const position = project.projectNodes.projectAnalyses.find(p => p.analysisId === a.id);
      if (position) {
        nodes.push({
          id: a.id,
          type: 'analysis',
          position: { x: position.xPosition, y: position.yPosition },
          data: {
            analysisId: a.id,
            projectId: projectId,
            openTab,
          },
        });
      }
    });

    // Add model entity nodes
    project.graph.modelEntities.forEach((me) => {
      const position = project.projectNodes.projectModelEntities.find(p => p.modelEntityId === me.id);
      if (position) {
        nodes.push({
          id: me.id,
          type: 'modelEntity',
          position: { x: position.xPosition, y: position.yPosition },
          data: {
            modelEntityId: me.id,
            projectId: projectId,
            openTab,
          },
        });
      }
    });

    return nodes;

  }, [project?.graph, project?.projectNodes, projectId, openTab]);

  // Memoize edges - uses current node positions from state for live updates during dragging
  const memoizedEdges = useMemo(() => {
    if (!project?.graph || nodes.length === 0) {
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

    // Helper to process all output connections for an entity
    const processEntityOutputs = (
      entityId: UUID,
      outputs: {
        dataSources: UUID[];
        datasets: UUID[];
        analyses: UUID[];
        pipelines: UUID[];
        modelEntities: UUID[];
      },
      entityType: 'dataSource' | 'dataset' | 'analysis' | 'pipeline' | 'modelEntity'
    ): Edge[] => {
      const edges: Edge[] = [];

      // Process all outgoing connections (outputs)
      const outgoingConnections = [
        { targets: outputs.dataSources, type: entityType },
        { targets: outputs.datasets, type: entityType },
        { targets: outputs.analyses, type: entityType },
        { targets: outputs.pipelines, type: entityType },
        { targets: outputs.modelEntities, type: entityType },
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
      ...project.graph.dataSources.flatMap(ds => processEntityOutputs(ds.id, ds.toEntities, 'dataSource')),
      ...project.graph.datasets.flatMap(d => processEntityOutputs(d.id, d.toEntities, 'dataset')),
      ...project.graph.analyses.flatMap(a => processEntityOutputs(a.id, a.toEntities, 'analysis')),
      ...project.graph.pipelines.flatMap(p => [
        ...processEntityOutputs(p.id, p.toEntities, 'pipeline'),
        ...p.runs.flatMap(run => processEntityOutputs(p.id, run.toEntities, 'pipeline'))
      ]),
      ...project.graph.modelEntities.flatMap(m => processEntityOutputs(m.id, m.toEntities, 'modelEntity')),
    ];

    return allEdges;
  }, [project?.graph, getEdgeColor, nodes]);

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
    if (!project?.graph || !node || !node.id) return;

    // Determine entity type by checking which list contains the node ID
    let entityType: "data_source" | "dataset" | "analysis" | "pipeline" | "model_entity" | null = null;

    if (project.graph.dataSources.some(ds => ds.id === node.id)) {
      entityType = "data_source";
    } else if (project.graph.datasets.some(ds => ds.id === node.id)) {
      entityType = "dataset";
    } else if (project.graph.analyses.some(a => a.id === node.id)) {
      entityType = "analysis";
    } else if (project.graph.pipelines.some(p => p.id === node.id)) {
      entityType = "pipeline";
    } else if (project.graph.modelEntities.some(me => me.id === node.id)) {
      entityType = "model_entity";
    }

    if (entityType) {
      updatePosition({
        projectId: project.id,
        entityType,
        entityId: node.id as UUID,
        xPosition: node.position.x,
        yPosition: node.position.y,
      });
    }
  }, [project?.graph, project?.id, updatePosition]);

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
        // onSelectionChange={handleSelectionChange}
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

export default function EntityRelationshipDiagram({ projectId, openTab }: EntityRelationshipDiagramProps) {
  return (
    <ReactFlowProvider>
      <EntityRelationshipDiagramContent projectId={projectId} openTab={openTab} />
    </ReactFlowProvider>
  );
}