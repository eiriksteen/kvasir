import React, { useCallback, useState, useEffect, useMemo } from 'react';
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
// import DataVisualizer from '@/components/data-visualization/DataVisualizer';
// import AnalysisItem from '@/components/analysis/AnalysisItem';
import { FrontendNode } from '@/types/node';
import DatasetBox from '@/app/projects/[projectId]/_components/erd/DatasetBox';
import AnalysisBox from '@/app/projects/[projectId]/_components/erd/AnalysisBox';
import TransportEdge from '@/app/projects/[projectId]/_components/erd/TransportEdge';
import { useProjectDataSources } from '@/hooks/useDataSources';
import DataSourceBox from '@/app/projects/[projectId]/_components/erd/DataSourceBox';
import { DataSource } from '@/types/data-sources';
import FileInfoModal from '@/components/info-modals/FileInfoModal';
import { Dataset } from '@/types/data-objects';
import DatasetInfoModal from '@/components/info-modals/DatasetInfoModal';
import { AnalysisJobResultMetadata } from '@/types/analysis';
import PipelineBox from '@/app/projects/[projectId]/_components/erd/PipelineBox';
import { Pipeline } from '@/types/pipeline';
import PipelineInfoModal from '@/components/info-modals/PipelineInfoModal';
import { UUID } from 'crypto';
import { ModelEntity } from '@/types/model';
import { useModelEntities } from '@/hooks/useModelEntities';
import ModelEntityBox from '@/app/projects/[projectId]/_components/erd/ModelEntityBox';
import ModelInfoModal from '@/components/info-modals/ModelInfoModal';
import { useProjectGraph } from '@/hooks/useProjectGraph';

const DataSourceNodeWrapper = ({ data }: { data: { dataSource: DataSource; gradientClass: string; onClick: () => void } }) => (
  <>
    <DataSourceBox
      dataSource={data.dataSource}
      gradientClass={data.gradientClass}
      onClick={data.onClick}
    />
    <Handle type="target" position={Position.Left} style={{ background: '#6b7280' }} />
    <Handle type="source" position={Position.Right} style={{ background: '#6b7280' }} />
  </>
);

// Wrapper component to adapt ReactFlow node props to Dataset component props
const DatasetNodeWrapper = ({ data }: { data: { dataset: Dataset; onClick: () => void } }) => (
  <>
    <DatasetBox
      dataset={data.dataset}
      onClick={data.onClick}
    />
    <Handle type="target" position={Position.Left} style={{ background: '#0E4F70' }} />
    <Handle type="source" position={Position.Right} style={{ background: '#0E4F70' }} />
  </>
);

// Wrapper component to adapt ReactFlow node props to Analysis component props
const AnalysisNodeWrapper = ({ data }: { data: { analysis: AnalysisJobResultMetadata; onClick: () => void } }) => (
  <>
  <AnalysisBox
    analysis={data.analysis}
    onClick={data.onClick}
  />
  <Handle type="target" position={Position.Left} style={{ background: '#004806' }} />
  <Handle type="source" position={Position.Right} style={{ background: '#004806' }} />
  </>
);

const PipelineNodeWrapper = ({ data }: { data: { pipeline: Pipeline; onClick: () => void, handleRunClick: () => void } }) => (
  <>
    <PipelineBox
      pipeline={data.pipeline}
      onClick={data.onClick}
      handleRunClick={data.handleRunClick}
    />
    <Handle type="target" position={Position.Left} style={{ background: '#840B08' }} />
    <Handle type="source" position={Position.Right} style={{ background: '#840B08' }} />
  </>
);

const ModelEntityNodeWrapper = ({ data }: { data: { modelEntity: ModelEntity; onClick: () => void } }) => (
  <>
    <ModelEntityBox
      modelEntity={data.modelEntity}
      onClick={data.onClick}
    />
    <Handle type="target" position={Position.Left} style={{ background: '#491A32' }} />
    <Handle type="source" position={Position.Right} style={{ background: '#491A32' }} />
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

  const getEdgeColor = (sourceType: string): string => {
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
  };

  const { project, frontendNodes, updatePosition } = useProject(projectId);
  const { dataSources } = useProjectDataSources(projectId);
  const { datasets } = useDatasets(projectId);
  const { pipelines, triggerRunPipeline } = usePipelines(projectId);
  const { modelEntities } = useModelEntities(projectId);
  const { analysisJobResults } = useAnalysis();
  const { projectGraph } = useProjectGraph(projectId);

  // const [selectedAnalysis, setSelectedAnalysis] = useState<string | null>(null);
  const [selectedDataSource, setSelectedDataSource] = useState<DataSource | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null);
  const [selectedModelEntity, setSelectedModelEntity] = useState<ModelEntity | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  console.log(projectGraph);

  // Memoize nodes
  const memoizedNodes = useMemo(() => {
    if (!project || !datasets || !analysisJobResults || !dataSources || !pipelines || !modelEntities) {
      return [];
    }

    const dataSourceNodes = frontendNodes.map((frontendNode: FrontendNode) => {
      const dataSource = dataSources.find(d => d.id === frontendNode.dataSourceId);
      if (!dataSource) return null;
      return {
        id: frontendNode.id,
        type: 'dataSource',
        position: { x: frontendNode.xPosition, y: frontendNode.yPosition },
        data: {
          label: dataSource.name,
          id: frontendNode.dataSourceId,
          dataSource: dataSource,
          onClick: () => setSelectedDataSource(dataSource)
        },
      } as Node;
    });

    const datasetNodes = frontendNodes.map((frontendNode: FrontendNode) => {
      const dataset = datasets.find(d => d.id === frontendNode.datasetId);
      if (!dataset) return null;
      return {
        id: frontendNode.id,
        type: 'dataset',
        position: { x: frontendNode.xPosition, y: frontendNode.yPosition },
        data: {
          label: dataset.name,
          id: frontendNode.datasetId,
          dataset: dataset,
          onClick: () => setSelectedDataset(dataset)
        },
      } as Node;
    });

    const pipelineNodes = frontendNodes.map((frontendNode: FrontendNode) => {

      const pipeline = pipelines.find(p => p.id === frontendNode.pipelineId);
      if (!pipeline) return null;
      return {
        id: frontendNode.id,
        type: 'pipeline',
        position: { x: frontendNode.xPosition, y: frontendNode.yPosition },
        data: {
          label: pipeline.name,
          id: frontendNode.pipelineId,
          pipeline: pipeline,
          onClick: () => setSelectedPipeline(pipeline),
          handleRunClick: () => triggerRunPipeline({projectId: projectId, pipelineId: pipeline.id})
        },
      } as Node;
    });

    const analysisNodes = frontendNodes.map((frontendNode: FrontendNode) => {
      const analysis = analysisJobResults.find(a => a.jobId === frontendNode.analysisId);
      if (!analysis) return null;
      return {
        id: frontendNode.id,
        type: 'analysis',
        position: { x: frontendNode.xPosition, y: frontendNode.yPosition },
        data: {
          label: analysis.name,
          id: frontendNode.analysisId,
          analysis: analysis,
          onClick: () => {} // TODO: Implement analysis modal when available
        },
      } as Node;
    });

    const modelEntityNodes = frontendNodes.map((frontendNode: FrontendNode) => {
      const modelEntity = modelEntities.find(m => m.id === frontendNode.modelEntityId);
      if (!modelEntity) return null;
      return {
        id: frontendNode.id,
        type: 'modelEntity',
        position: { x: frontendNode.xPosition, y: frontendNode.yPosition },
        data: {
          label: modelEntity.name,
          id: frontendNode.modelEntityId,
          modelEntity: modelEntity,
          onClick: () => setSelectedModelEntity(modelEntity)
        },
      } as Node;
    });

    return [...datasetNodes.filter(Boolean), ...analysisNodes.filter(Boolean), ...dataSourceNodes.filter(Boolean), ...pipelineNodes.filter(Boolean), ...modelEntityNodes.filter(Boolean)] as Node[];

  }, [project, datasets, analysisJobResults, frontendNodes, dataSources, pipelines, modelEntities, triggerRunPipeline, projectId]);

  // Memoize edges
  const memoizedEdges = useMemo(() => {
    if (!project || !projectGraph || !frontendNodes) {
      return [];
    }
    const dataSourcesToDatasetsEdges = projectGraph?.dataSources
      .flatMap(dataSource =>
        dataSource.toDatasets.map(datasetId => {
          const sourceNode = frontendNodes.find(fn => fn.dataSourceId === dataSource.id);
          const targetNode = frontendNodes.find(fn => fn.datasetId === datasetId);
          if (!sourceNode?.id || !targetNode?.id) return null;
          return {
            id: String(`${dataSource.id}->${datasetId}`),
            source: sourceNode.id,
            target: targetNode.id,
            type: 'default',
            animated: true,
            style: { stroke: getEdgeColor('dataSource'), strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed },

          } as Edge;
        })
      )
      .filter(Boolean) as Edge[];

    const datasetsToAnalysesEdges = projectGraph?.datasets
      .flatMap(dataset =>
        dataset.toAnalyses.map(analysisId => {
          const sourceNode = frontendNodes.find(fn => fn.datasetId === dataset.id);
          const targetNode = frontendNodes.find(fn => fn.analysisId === analysisId);
          if (!sourceNode?.id || !targetNode?.id) return null;
          return {
            id: String(`${dataset.id}->${analysisId}`),
            source: sourceNode.id,
            target: targetNode.id,
            type: 'default',
            animated: true,
            style: { stroke: getEdgeColor('dataset'), strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed },
          } as Edge;
        })
      )
      .filter(Boolean) as Edge[];

    const datasetsToPipelinesEdges = projectGraph?.datasets
      .flatMap(dataset =>
        dataset.toPipelines.map(pipelineId => {
          const sourceNode = frontendNodes.find(fn => fn.datasetId === dataset.id);
          const targetNode = frontendNodes.find(fn => fn.pipelineId === pipelineId);
          if (!sourceNode?.id || !targetNode?.id) return null;
          return {
            id: String(`${dataset.id}->${pipelineId}`),
            source: sourceNode.id,
            target: targetNode.id,
            type: 'default',
            animated: true,
            style: { stroke: getEdgeColor('dataset'), strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed },
          } as Edge;
        })
      )
      .filter(Boolean) as Edge[];

    const modelEntitiesToPipelinesEdges = projectGraph?.modelEntities
      .flatMap(modelEntity =>
        modelEntity.toPipelines.map(pipelineId => {
          const sourceNode = frontendNodes.find(fn => fn.modelEntityId === modelEntity.id);
          const targetNode = frontendNodes.find(fn => fn.pipelineId === pipelineId);
          if (!sourceNode?.id || !targetNode?.id) return null;
          return {
            id: String(`${modelEntity.id}->${pipelineId}`),
            source: sourceNode.id,
            target: targetNode.id,
            type: 'default',
            animated: true,
            style: { stroke: getEdgeColor('modelEntity'), strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed },
          } as Edge;
        })
      )
      .filter(Boolean) as Edge[];

    const pipelinesToDatasetsEdges = projectGraph?.pipelines
      .flatMap(pipeline =>
        pipeline.toDatasets.map(datasetId => {
          const sourceNode = frontendNodes.find(fn => fn.pipelineId === pipeline.id);
          const targetNode = frontendNodes.find(fn => fn.datasetId === datasetId);
          if (!sourceNode?.id || !targetNode?.id) return null;
          return {
            id: String(`${pipeline.id}->${datasetId}`),
            source: sourceNode.id,
            target: targetNode.id,
            type: 'default',
            animated: true,
            style: { stroke: getEdgeColor('pipeline'), strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed },
          } as Edge;
        })
      )
      .filter(Boolean) as Edge[];

    const pipelinesToModelEntitiesEdges = projectGraph?.pipelines
      .flatMap(pipeline =>
        pipeline.toModelEntities.map(modelEntityId => {
          const sourceNode = frontendNodes.find(fn => fn.pipelineId === pipeline.id);
          const targetNode = frontendNodes.find(fn => fn.modelEntityId === modelEntityId);
          if (!sourceNode?.id || !targetNode?.id) return null;
          return {
            id: String(`${pipeline.id}->${modelEntityId}`),
            source: sourceNode.id,
            target: targetNode.id,
            type: 'default',
            animated: true,
            style: { stroke: getEdgeColor('pipeline'), strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed },
          } as Edge;
        })
      )
      .filter(Boolean) as Edge[];


    return [...dataSourcesToDatasetsEdges, ...datasetsToAnalysesEdges, ...datasetsToPipelinesEdges, ...modelEntitiesToPipelinesEdges, ...pipelinesToDatasetsEdges, ...pipelinesToModelEntitiesEdges];
  }, [project, frontendNodes, projectGraph]);

  // console.log(frontendNodes);
  // console.log(memoizedEdges);

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
    const frontendNode = frontendNodes.find(fn => fn.id === node.id);
    if (frontendNode) {
      updatePosition({
        ...frontendNode,
        xPosition: node.position.x,
        yPosition: node.position.y,
      });
    }
  }, [frontendNodes, updatePosition]);


  // These are needed to ensure we don't need to click esc twice to close the modals

  const handleCloseDatasetModal = useCallback(() => {
    setSelectedDataset(null);
  }, []);

  const handleCloseDataSourceModal = useCallback(() => {
    setSelectedDataSource(null);
  }, []);

  const handleClosePipelineModal = useCallback(() => {
    setSelectedPipeline(null);
  }, []);

  const handleCloseModelEntityModal = useCallback(() => {
    setSelectedModelEntity(null);
  }, []);

  return (
    <div className="w-full h-screen">
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
      {/* {renderModal()} */}
      {selectedDataSource && <FileInfoModal dataSourceId={selectedDataSource.id} onClose={handleCloseDataSourceModal} />}
      {selectedDataset && <DatasetInfoModal datasetId={selectedDataset.id} onClose={handleCloseDatasetModal} projectId={projectId} />}
      {selectedPipeline && <PipelineInfoModal pipelineId={selectedPipeline.id} onClose={handleClosePipelineModal} />}
      {/* TODO: Add AnalysisInfoModal when available */}
      {selectedModelEntity && <ModelInfoModal modelEntityId={selectedModelEntity.id} onClose={handleCloseModelEntityModal} projectId={projectId} />}
    </div>
  );
};
