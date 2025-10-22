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
    Position
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useProject } from '@/hooks/useProject';
import { useDatasets, useAnalysis, usePipelines } from '@/hooks';
import { 
  ProjectDataSourceInDB, 
  ProjectDatasetInDB, 
  ProjectAnalysisInDB, 
  ProjectPipelineInDB, 
  ProjectModelEntityInDB 
} from '@/types/project';
import DatasetBox from '@/app/projects/[projectId]/_components/erd/DatasetBox';
import AnalysisBox from '@/app/projects/[projectId]/_components/erd/AnalysisBox';
import TransportEdge from '@/app/projects/[projectId]/_components/erd/TransportEdge';
import { useProjectDataSources } from '@/hooks/useDataSources';
import DataSourceBox from '@/app/projects/[projectId]/_components/erd/DataSourceBox';
import PipelineBox from '@/app/projects/[projectId]/_components/erd/PipelineBox';
import { Pipeline, PipelineRunInDB } from '@/types/pipeline';
import { UUID } from 'crypto';
import { ModelEntity } from '@/types/model';
import { useModelEntities } from '@/hooks/useModelEntities';
import ModelEntityBox from '@/app/projects/[projectId]/_components/erd/ModelEntityBox';
import { useProjectGraph } from '@/hooks/useProjectGraph';
import { computeBoxEdgeLocations } from '@/app/projects/[projectId]/_components/erd/computeBoxEdgeLocations';
import { useTabContext } from '@/hooks/useTabContext';
import { DataSource } from '@/types/data-sources';
import { Dataset } from '@/types/data-objects';
import { AnalysisObjectSmall } from '@/types/analysis';

const DataSourceNodeWrapper = ({ data }: { data: { dataSource: DataSource; gradientClass: string; onClick: () => void } }) => (
  <>
    <DataSourceBox
      dataSource={data.dataSource}
      gradientClass={data.gradientClass}
      onClick={data.onClick}
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
const DatasetNodeWrapper = ({ data }: { data: { dataset: Dataset; onClick: () => void } }) => (
  <>
    <DatasetBox
      dataset={data.dataset}
      onClick={data.onClick}
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
const AnalysisNodeWrapper = ({ data }: { data: { analysis: AnalysisObjectSmall; onClick: () => void } }) => (
  <>
  <AnalysisBox
    analysis={data.analysis}
    onClick={data.onClick}
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

const PipelineNodeWrapper = ({ data }: { data: { pipeline: Pipeline; onClick: () => void, handleRunClick: () => void, pipelineRuns: PipelineRunInDB[] } }) => (
  <>
    <PipelineBox
      pipeline={data.pipeline}
      onClick={data.onClick}
      handleRunClick={data.handleRunClick}
      pipelineRuns={data.pipelineRuns}
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

const ModelEntityNodeWrapper = ({ data }: { data: { modelEntity: ModelEntity; onClick: () => void } }) => (
  <>
    <ModelEntityBox
      modelEntity={data.modelEntity}
      onClick={data.onClick}
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

export default function EntityRelationshipDiagram({ projectId }: EntityRelationshipDiagramProps) {

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

  const { project, updatePosition } = useProject(projectId);
  const { dataSources } = useProjectDataSources(projectId);
  const { datasets } = useDatasets(projectId);
  const { pipelines, triggerRunPipeline, pipelineRuns } = usePipelines(projectId);
  const { modelEntities } = useModelEntities(projectId);
  const { analysisObjects } = useAnalysis(projectId);
  const { projectGraph } = useProjectGraph(projectId);
  const { openTab, setProjectTabLabel } = useTabContext(projectId);
  
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Update project tab label when project name changes
  useEffect(() => {
    if (project?.name) {
      setProjectTabLabel('');
    }
  }, [project?.name, setProjectTabLabel]);

  // Handler to open tabs
  const handleOpenTab = useCallback(
    ({ type, id, label }: { type: 'data_source' | 'dataset' | 'analysis' | 'pipeline' | 'model_entity'; id: string; label: string }) => {
      openTab({ type, id, label, closable: true });
    },
    [openTab]
  );

  // Memoize nodes
  const memoizedNodes = useMemo(() => {
    if (!project || !datasets || !analysisObjects || !dataSources || !pipelines || !modelEntities) {
      return [];
    }

    const nodes: Node[] = [];

    // Add data source nodes
    project.dataSources.forEach((projectDataSource: ProjectDataSourceInDB) => {
      const dataSource = dataSources.find(d => d.id === projectDataSource.dataSourceId);
      if (dataSource) {
        nodes.push({
          id: projectDataSource.dataSourceId,
          type: 'dataSource',
          position: { x: projectDataSource.xPosition, y: projectDataSource.yPosition },
          data: {
            label: dataSource.name,
            id: projectDataSource.dataSourceId,
            dataSource: dataSource,
            onClick: () => handleOpenTab({ type: 'data_source', id: dataSource.id, label: dataSource.name })
          },
        });
      }
    });

    // Add dataset nodes
    project.datasets.forEach((projectDataset: ProjectDatasetInDB) => {
      const dataset = datasets.find(d => d.id === projectDataset.datasetId);
      if (dataset) {
        nodes.push({
          id: projectDataset.datasetId,
          type: 'dataset',
          position: { x: projectDataset.xPosition, y: projectDataset.yPosition },
          data: {
            label: dataset.name,
            id: projectDataset.datasetId,
            dataset: dataset,
            onClick: () => handleOpenTab({ type: 'dataset', id: dataset.id, label: dataset.name })
          },
        });
      }
    });

    // Add pipeline nodes
    project.pipelines.forEach((projectPipeline: ProjectPipelineInDB) => {
      const pipeline = pipelines.find(p => p.id === projectPipeline.pipelineId);
      if (pipeline) {
        nodes.push({
          id: projectPipeline.pipelineId,
          type: 'pipeline',
          position: { x: projectPipeline.xPosition, y: projectPipeline.yPosition },
          data: {
            label: pipeline.name,
            id: projectPipeline.pipelineId,
            pipeline: pipeline,
            onClick: () => handleOpenTab({ type: 'pipeline', id: pipeline.id, label: pipeline.name }),
            handleRunClick: () => triggerRunPipeline({projectId: projectId, pipelineId: pipeline.id}),
            pipelineRuns: pipelineRuns.filter((p: PipelineRunInDB) => p.pipelineId === pipeline.id)
          },
        });
      }
    });

    // Add analysis nodes
    project.analyses.forEach((projectAnalysis: ProjectAnalysisInDB) => {
      const analysisObject = analysisObjects.find(a => a.id === projectAnalysis.analysisId);
      if (analysisObject) {
        nodes.push({
          id: projectAnalysis.analysisId,
          type: 'analysis',
          position: { x: projectAnalysis.xPosition, y: projectAnalysis.yPosition },
          data: {
            label: analysisObject.name,
            id: projectAnalysis.analysisId,
            analysis: analysisObject,
            onClick: () => handleOpenTab({ type: 'analysis', id: analysisObject.id, label: analysisObject.name })
          },
        });
      }
    });

    // Add model entity nodes
    project.modelEntities.forEach((projectModelEntity: ProjectModelEntityInDB) => {
      const modelEntity = modelEntities.find(m => m.id === projectModelEntity.modelEntityId);
      if (modelEntity) {
        nodes.push({
          id: projectModelEntity.modelEntityId,
          type: 'modelEntity',
          position: { x: projectModelEntity.xPosition, y: projectModelEntity.yPosition },
          data: {
            label: modelEntity.name,
            id: projectModelEntity.modelEntityId,
            modelEntity: modelEntity,
            onClick: () => handleOpenTab({ type: 'model_entity', id: modelEntity.id, label: modelEntity.name })
          },
        });
      }
    });

    return nodes;

  }, [project, datasets, analysisObjects, dataSources, pipelines, modelEntities, handleOpenTab, triggerRunPipeline, projectId, pipelineRuns]);

  // Memoize edges - uses current node positions from nodes state
  const memoizedEdges = useMemo(() => {
    if (!projectGraph || nodes.length === 0) {
      return [];
    }

    // Helper to get entity position from nodes or graph data
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

  // Only update nodes when memoizedNodes changes
  useEffect(() => {
    setNodes((prevNodes) => {
      const prev = JSON.stringify(prevNodes);
      const next = JSON.stringify(memoizedNodes);
      return prev === next ? prevNodes : memoizedNodes;
    });
  }, [memoizedNodes, setNodes]);

  // Only update edges when memoizedEdges changes
  useEffect(() => {
    setEdges((prevEdges) => {
      const prev = JSON.stringify(prevEdges);
      const next = JSON.stringify(memoizedEdges);
      return prev === next ? prevEdges : memoizedEdges;
    });
  }, [memoizedEdges, setEdges]);


  const handleNodeDragStop = useCallback((event: React.MouseEvent, node: Node) => {
    if (!project) return;

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
        fitView
        onNodeDragStop={handleNodeDragStop}
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