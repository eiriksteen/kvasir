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
import { useDatasets, useAnalysis } from '@/hooks';
// import DataVisualizer from '@/components/data-visualization/DataVisualizer';
// import AnalysisItem from '@/components/analysis/AnalysisItem';
import { FrontendNode } from '@/types/node';
import Dataset from '@/components/datasets/Dataset';
import AnalysisNode from '@/components/react-flow-components/AnalysisNode';
import TransportEdge from '@/components/react-flow-components/TransportEdge';
import { useDataSources } from '@/hooks/useDataSources';
import DataSourceBox from '../data-sources/DataSourceBox';
import { DataSource } from '@/types/data-integration';
import FileInfoModal from '@/components/data-sources/FileInfoModal';

const DataSourceNodeWrapper = ({ data }: { data: { dataSource: DataSource; gradientClass: string; onClick: () => void } }) => (
  <DataSourceBox 
    dataSource={data.dataSource} 
    gradientClass={data.gradientClass} 
    onClick={data.onClick} 
  />
);

// Wrapper component to adapt ReactFlow node props to Dataset component props
const DatasetNodeWrapper = ({ data }: { data: { label: string; id: string; onClick: () => void } }) => (
  <Dataset 
    datasetId={data.id} 
    gradientClass="from-blue-500 to-purple-600" 
    defaultView="mini" 
  />
);

const nodeTypes = {
  dataset: DatasetNodeWrapper,
  analysis: AnalysisNode,
  dataSource: DataSourceNodeWrapper,
};

const edgeTypes: EdgeTypes = {
  'custom-edge': TransportEdge,
};

interface ProjectViewProps {
  projectId: string;
}

const ProjectView: React.FC<ProjectViewProps> = ({ projectId }) => {
  const { selectedProject, frontendNodes, updatePosition } = useProject(projectId);
  const { dataSources } = useDataSources();
  const { datasets } = useDatasets();
  const { analysisJobResults } = useAnalysis();
  // const [selectedAnalysis, setSelectedAnalysis] = useState<string | null>(null);
  const [selectedDataSource, setSelectedDataSource] = useState<DataSource | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Memoize nodes
  const memoizedNodes = useMemo(() => {
    if (!selectedProject || !datasets || !analysisJobResults?.analysesJobResults || !dataSources) {
      return [];
    }

    const dataSourceNodes = frontendNodes.map((frontendNode: FrontendNode) => {
      const dataSource = dataSources.filter(d => selectedProject.dataSourceIds.includes(d.id)).find(d => d.id === frontendNode.dataSourceId);
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
      const dataset = datasets.filter(d => selectedProject.datasetIds.includes(d.id)).find(d => d.id === frontendNode.datasetId);
      if (!dataset) return null;
      return {
        id: frontendNode.id,
        type: 'dataset',
        position: { x: frontendNode.xPosition, y: frontendNode.yPosition },
        data: {
          label: dataset.name,
          id: frontendNode.datasetId,
        },
      } as Node;
    });

    const analysisNodes = frontendNodes.map((frontendNode: FrontendNode) => {
      const analysis = analysisJobResults.analysesJobResults.filter(a => selectedProject.analysisIds.includes(a.jobId)).find(a => a.jobId === frontendNode.analysisId);
      if (!analysis) return null;
      return {
        id: frontendNode.id,
        type: 'analysis',
        position: { x: frontendNode.xPosition, y: frontendNode.yPosition },
        data: {
          label: analysis.name,
          id: frontendNode.analysisId,
          // onClick: () => setSelectedAnalysis(frontendNode.analysisId)
        },
      } as Node;
    });

    return [...datasetNodes.filter(Boolean), ...analysisNodes.filter(Boolean), ...dataSourceNodes.filter(Boolean)] as Node[];

  }, [selectedProject, datasets, analysisJobResults, frontendNodes, dataSources]);

  // Memoize edges
  const memoizedEdges = useMemo(() => {
    if (!selectedProject || !analysisJobResults?.analysesJobResults) {
      return [];
    }
    return analysisJobResults.analysesJobResults
      .filter(analysis => selectedProject.analysisIds.includes(analysis.jobId))
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
  }, [selectedProject, frontendNodes, analysisJobResults]);

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


  // const renderModal = () => {

  //   // Dataset modal is opened inside the Dataset component

  //   if (selectedAnalysis) {
  //     const analysis = analysisJobResults?.analysesJobResults.find(a => a.jobId === selectedAnalysis);
  //     if (!analysis) return null;

  //     return (
  //       <AnalysisItem
  //         analysis={analysis}
  //         isSelected={false}
  //         onClick={() => {}}
  //         isModal={true}
  //         onClose={() => setSelectedAnalysis(null)}
  //       />
  //     );
  //   }

  //   return null;
  // };

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
      {selectedDataSource && <FileInfoModal dataSource={selectedDataSource} setSelectedDataSource={setSelectedDataSource} />}
    </div>
  );
};

export default ProjectView;
