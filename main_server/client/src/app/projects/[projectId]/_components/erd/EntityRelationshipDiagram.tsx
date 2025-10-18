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
      const analysis = analysisObjects.analysisObjects.find(a => a.id === projectAnalysis.analysisId);
      if (analysis) {
        nodes.push({
          id: projectAnalysis.analysisId,
          type: 'analysis',
          position: { x: projectAnalysis.xPosition, y: projectAnalysis.yPosition },
          data: {
            label: analysis.name,
            id: projectAnalysis.analysisId,
            analysis: analysis,
            onClick: () => handleOpenTab({ type: 'analysis', id: analysis.id, label: analysis.name })
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
    if (!project || !projectGraph || nodes.length === 0) {
      return [];
    }

    // Helper to get entity with current position from nodes state
    const getEntityWithCurrentPosition = (entityId: UUID): { xPosition: number, yPosition: number } | null => {
      // Find entity in project - check each entity type
      const dataSource = project.dataSources.find(ds => ds.dataSourceId === entityId);
      if (dataSource) {
        const currentNode = nodes.find(n => n.id === entityId);
        return currentNode ? { xPosition: currentNode.position.x, yPosition: currentNode.position.y } : { xPosition: dataSource.xPosition, yPosition: dataSource.yPosition };
      }

      const dataset = project.datasets.find(ds => ds.datasetId === entityId);
      if (dataset) {
        const currentNode = nodes.find(n => n.id === entityId);
        return currentNode ? { xPosition: currentNode.position.x, yPosition: currentNode.position.y } : { xPosition: dataset.xPosition, yPosition: dataset.yPosition };
      }

      const analysis = project.analyses.find(a => a.analysisId === entityId);
      if (analysis) {
        const currentNode = nodes.find(n => n.id === entityId);
        return currentNode ? { xPosition: currentNode.position.x, yPosition: currentNode.position.y } : { xPosition: analysis.xPosition, yPosition: analysis.yPosition };
      }

      const pipeline = project.pipelines.find(p => p.pipelineId === entityId);
      if (pipeline) {
        const currentNode = nodes.find(n => n.id === entityId);
        return currentNode ? { xPosition: currentNode.position.x, yPosition: currentNode.position.y } : { xPosition: pipeline.xPosition, yPosition: pipeline.yPosition };
      }

      const modelEntity = project.modelEntities.find(me => me.modelEntityId === entityId);
      if (modelEntity) {
        const currentNode = nodes.find(n => n.id === entityId);
        return currentNode ? { xPosition: currentNode.position.x, yPosition: currentNode.position.y } : { xPosition: modelEntity.xPosition, yPosition: modelEntity.yPosition };
      }

      return null;
    };

    const dataSourcesToDatasetsEdges = projectGraph?.dataSources
      .flatMap(dataSource =>
        dataSource.toDatasets.map(datasetId => {
          const sourceEntity = getEntityWithCurrentPosition(dataSource.id);
          const targetEntity = getEntityWithCurrentPosition(datasetId);
          if (!sourceEntity || !targetEntity) return null;
          const edgeLocation = computeBoxEdgeLocations(sourceEntity, targetEntity);
          return {
            id: String(`${dataSource.id}->${datasetId}`),
            source: dataSource.id,
            target: datasetId,
            type: 'default',
            animated: true,
            style: { stroke: getEdgeColor('dataSource'), strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed },
            sourceHandle: edgeLocation.from,
            targetHandle: edgeLocation.to,

          } as Edge;
        })
      )
      .filter(Boolean) as Edge[];

    const datasetsToAnalysesEdges = projectGraph?.analyses
      .flatMap(analysis =>
        analysis.fromDatasets.map(datasetId => {
          const sourceEntity = getEntityWithCurrentPosition(datasetId);
          const targetEntity = getEntityWithCurrentPosition(analysis.id);
          if (!sourceEntity || !targetEntity) return null;
          const edgeLocation = computeBoxEdgeLocations(sourceEntity, targetEntity);
          return {
            id: String(`${datasetId}->${analysis.id}`),
            source: datasetId,
            target: analysis.id,
            type: 'default',
            animated: true,
            style: { stroke: getEdgeColor('dataset'), strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed },
            sourceHandle: edgeLocation.from,
            targetHandle: edgeLocation.to,
          } as Edge;
        })
      )
      .filter(Boolean) as Edge[];
    
    const dataSourcesToAnalysesEdges = projectGraph?.analyses
      .flatMap(analysis =>
        analysis.fromDataSources.map(dataSourceId => {
          const sourceEntity = getEntityWithCurrentPosition(dataSourceId);
          const targetEntity = getEntityWithCurrentPosition(analysis.id);
          if (!sourceEntity || !targetEntity) return null;
          const edgeLocation = computeBoxEdgeLocations(sourceEntity, targetEntity);
          return {
            id: String(`${dataSourceId}->${analysis.id}`),
            source: dataSourceId,
            target: analysis.id,
            type: 'default',
            animated: true,
            style: { stroke: getEdgeColor('dataset'), strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed },
            sourceHandle: edgeLocation.from,
            targetHandle: edgeLocation.to,
          } as Edge;
        })
      )
      .filter(Boolean) as Edge[];

    const datasetsToPipelinesEdges = projectGraph?.datasets
      .flatMap(dataset =>
        dataset.toPipelines.map(pipelineId => {
          const sourceEntity = getEntityWithCurrentPosition(dataset.id);
          const targetEntity = getEntityWithCurrentPosition(pipelineId);
          if (!sourceEntity || !targetEntity) return null;
          const edgeLocation = computeBoxEdgeLocations(sourceEntity, targetEntity);
          return {
            id: String(`${dataset.id}->${pipelineId}`),
            source: dataset.id,
            target: pipelineId,
            type: 'default',
            animated: true,
            style: { stroke: getEdgeColor('dataset'), strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed },
            sourceHandle: edgeLocation.from,
            targetHandle: edgeLocation.to,
          } as Edge;
        })
      )
      .filter(Boolean) as Edge[];

    const modelEntitiesToPipelinesEdges = projectGraph?.modelEntities
      .flatMap(modelEntity =>
        modelEntity.toPipelines.map(pipelineId => {
          const sourceEntity = getEntityWithCurrentPosition(modelEntity.id);
          const targetEntity = getEntityWithCurrentPosition(pipelineId);
          if (!sourceEntity || !targetEntity) return null;
          const edgeLocation = computeBoxEdgeLocations(sourceEntity, targetEntity);
          return {
            id: String(`${modelEntity.id}->${pipelineId}`),
            source: modelEntity.id,
            target: pipelineId,
            type: 'default',
            animated: true,
            style: { stroke: getEdgeColor('modelEntity'), strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed },
            sourceHandle: edgeLocation.from,
            targetHandle: edgeLocation.to,
          } as Edge;
        })
      )
      .filter(Boolean) as Edge[];

    const pipelinesToDatasetsEdges = projectGraph?.pipelines
      .flatMap(pipeline =>
        pipeline.toDatasets.map(datasetId => {
          const sourceEntity = getEntityWithCurrentPosition(pipeline.id);
          const targetEntity = getEntityWithCurrentPosition(datasetId);
          if (!sourceEntity || !targetEntity) return null;
          const edgeLocation = computeBoxEdgeLocations(sourceEntity, targetEntity);
          return {
            id: String(`${pipeline.id}->${datasetId}`),
            source: pipeline.id,
            target: datasetId,
            type: 'default',
            animated: true,
            style: { stroke: getEdgeColor('pipeline'), strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed },
            sourceHandle: edgeLocation.from,
            targetHandle: edgeLocation.to,
          } as Edge;
        })
      )
      .filter(Boolean) as Edge[];

    const pipelinesToModelEntitiesEdges = projectGraph?.pipelines
      .flatMap(pipeline =>
        pipeline.toModelEntities.map(modelEntityId => {
          const sourceEntity = getEntityWithCurrentPosition(pipeline.id);
          const targetEntity = getEntityWithCurrentPosition(modelEntityId);
          if (!sourceEntity || !targetEntity) return null;
          const edgeLocation = computeBoxEdgeLocations(sourceEntity, targetEntity);
          return {
            id: String(`${pipeline.id}->${modelEntityId}`),
            source: pipeline.id,
            target: modelEntityId,
            type: 'default',
            animated: true,
            style: { stroke: getEdgeColor('pipeline'), strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed },
            sourceHandle: edgeLocation.from,
            targetHandle: edgeLocation.to,
          } as Edge;
        })
      )
      .filter(Boolean) as Edge[];


    return [
      ...dataSourcesToDatasetsEdges, 
      ...datasetsToAnalysesEdges, 
      ...dataSourcesToAnalysesEdges, 
      ...datasetsToPipelinesEdges, 
      ...modelEntitiesToPipelinesEdges, 
      ...pipelinesToDatasetsEdges, 
      ...pipelinesToModelEntitiesEdges];
  }, [project, projectGraph, getEdgeColor, nodes]);

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
