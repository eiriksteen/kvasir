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
    useEdgesState
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

const DataSourceNodeWrapper = ({ data }: { data: { dataSource: DataSource; gradientClass: string; onClick: () => void } }) => (
  <DataSourceBox 
    dataSource={data.dataSource} 
    gradientClass={data.gradientClass} 
    onClick={data.onClick} 
  />
);

// Wrapper component to adapt ReactFlow node props to Dataset component props
const DatasetNodeWrapper = ({ data }: { data: { dataset: Dataset; onClick: () => void } }) => (
  <DatasetBox 
    dataset={data.dataset} 
    onClick={data.onClick} 
  />
);

// Wrapper component to adapt ReactFlow node props to Analysis component props
const AnalysisNodeWrapper = ({ data }: { data: { analysis: AnalysisJobResultMetadata; onClick: () => void } }) => (
  <AnalysisBox 
    analysis={data.analysis} 
    onClick={data.onClick} 
  />
);

const PipelineNodeWrapper = ({ data }: { data: { pipeline: Pipeline; onClick: () => void } }) => (
  <PipelineBox 
    pipeline={data.pipeline} 
    onClick={data.onClick} 
  />
);

const nodeTypes = {
  dataset: DatasetNodeWrapper,
  analysis: AnalysisNodeWrapper,
  dataSource: DataSourceNodeWrapper,
  pipeline: PipelineNodeWrapper,
};

const edgeTypes: EdgeTypes = {
  'custom-edge': TransportEdge,
};

interface EntityRelationshipDiagramProps {
  projectId: UUID;
}

export default function EntityRelationshipDiagram({ projectId }: EntityRelationshipDiagramProps) {
  const { project, frontendNodes, updatePosition } = useProject(projectId);
  const { dataSources } = useProjectDataSources(projectId);
  const { datasets } = useDatasets(projectId);
  const { pipelines } = usePipelines(projectId);
  const { analysisJobResults } = useAnalysis();
  // const [selectedAnalysis, setSelectedAnalysis] = useState<string | null>(null);
  const [selectedDataSource, setSelectedDataSource] = useState<DataSource | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Memoize nodes
  const memoizedNodes = useMemo(() => {
    if (!project || !datasets || !analysisJobResults || !dataSources || !pipelines) {
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
          onClick: () => setSelectedPipeline(pipeline)
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

    return [...datasetNodes.filter(Boolean), ...analysisNodes.filter(Boolean), ...dataSourceNodes.filter(Boolean), ...pipelineNodes.filter(Boolean)] as Node[];

  }, [project, datasets, analysisJobResults, frontendNodes, dataSources, pipelines]);

  // Memoize edges
  const memoizedEdges = useMemo(() => {
    if (!project || !analysisJobResults) {
      return [];
    }
    return analysisJobResults
      .flatMap(analysis =>
        analysis.datasetIds.map(datasetId => {
          const sourceNode = frontendNodes.find(fn => fn.datasetId === datasetId);
          const targetNode = frontendNodes.find(fn => fn.analysisId === analysis.jobId);
          if (!sourceNode?.id || !targetNode?.id) return null;
          return {
            id: String(`e${datasetId}->${analysis.jobId}`),
            source: sourceNode.id,
            target: targetNode.id,
            type: 'default',
            animated: true,
            style: { stroke: '#6366f1', strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed },
          } as Edge;
        })
      )
      .filter(Boolean) as Edge[];
  }, [project, frontendNodes, analysisJobResults]);

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
          nodeColor="#6366f1"
          maskColor="rgba(0, 0, 0, 0.1)"
        /> */}
      </ReactFlow>
      {/* {renderModal()} */}
      {selectedDataSource && <FileInfoModal dataSourceId={selectedDataSource.id} onClose={handleCloseDataSourceModal} />}
      {selectedDataset && <DatasetInfoModal datasetId={selectedDataset.id} onClose={handleCloseDatasetModal} projectId={projectId} />}
      {selectedPipeline && <PipelineInfoModal pipelineId={selectedPipeline.id} onClose={handleClosePipelineModal} />}
      {/* TODO: Add AnalysisInfoModal when available */}
    </div>
  );
};
