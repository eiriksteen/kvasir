import React, { useCallback, useState, useEffect, useMemo } from 'react';
import {
    ReactFlow,
    Node,
    Background,
    Controls,
    MiniMap,
    EdgeTypes,
    MarkerType,
    Edge,
    useNodesState,
    useEdgesState
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useProject } from '@/hooks/useProject';
import { useDatasets, useAnalysis } from '@/hooks';
import DataVisualizer from './DataVisualizer';
import AnalysisItemSmall from './analysis/AnalysisItem';
import { X } from 'lucide-react';
import { FrontendNode } from '@/types/node';
import DatasetNode from './react-flow-components/DatasetNode';
import AnalysisNode from './react-flow-components/AnalysisNode';
import TransportEdge from './react-flow-components/TransportEdge';

const nodeTypes = {
  dataset: DatasetNode,
  analysis: AnalysisNode,
};

const edgeTypes: EdgeTypes = {
  'custom-edge': TransportEdge,
};


const ProjectView: React.FC = () => {
  const { selectedProject, frontendNodes, updatePosition } = useProject();
  const { datasets } = useDatasets();
  const { analysisJobResults } = useAnalysis();
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState<string | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  console.log("frontendNodes in ProjectView", frontendNodes);

  // Memoize nodes
  const memoizedNodes = useMemo(() => {
    if (!selectedProject || !datasets?.timeSeries || !analysisJobResults?.analysesJobResults) {
      return [];
    }
    const datasetNodes = frontendNodes.map((frontendNode: FrontendNode) => {
      const dataset = datasets.timeSeries.filter(d => selectedProject.datasetIds.includes(d.id)).find(d => d.id === frontendNode.datasetId);
      if (!dataset) return null;
      return {
        id: frontendNode.id,
        type: 'dataset',
        position: { x: frontendNode.xPosition, y: frontendNode.yPosition },
        data: {
          label: dataset.name,
          id: frontendNode.datasetId,
          onClick: () => setSelectedDataset(frontendNode.datasetId)
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
          onClick: () => setSelectedAnalysis(frontendNode.analysisId)
        },
      } as Node;
    });
    return [...datasetNodes.filter(Boolean), ...analysisNodes.filter(Boolean)] as Node[];
  }, [selectedProject, datasets, analysisJobResults, frontendNodes]);

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


  const handleNodeDragStop = useCallback((event: any, node: Node) => {
    const frontendNode = frontendNodes.find(fn => fn.id === node.id);
    if (frontendNode) {
      updatePosition({
        ...frontendNode,
        xPosition: node.position.x,
        yPosition: node.position.y,
      });
    }
  }, [frontendNodes, updatePosition]);


  const renderModal = () => {
    if (selectedDataset) {
      return (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="relative flex w-full max-w-5xl h-[80vh] bg-gray-950 border border-[#101827] rounded-lg shadow-2xl overflow-hidden">
            <button
              onClick={() => setSelectedDataset(null)}
              className="absolute top-3 right-3 z-50 p-1 rounded-full text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
              title="Close (Esc)"
            >
              <X size={20} />
            </button>
            <div className="flex-1 flex flex-col overflow-hidden bg-gray-950">
              <DataVisualizer />
            </div>
          </div>
        </div>
      );
    }

    if (selectedAnalysis) {
      const analysis = analysisJobResults?.analysesJobResults.find(a => a.jobId === selectedAnalysis);
      if (!analysis) return null;

      return (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/80 backdrop-blur-sm ">
          <div className="relative flex w-full max-w-5xl h-[80vh] bg-gray-950 border border-[#101827] rounded-lg shadow-2xl overflow-hidden">
            <button
              onClick={() => setSelectedAnalysis(null)}
              className="absolute top-3 right-3 z-50 p-1 rounded-full text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
              title="Close (Esc)"
            >
              <X size={20} />
            </button>
            <div className="flex-1 flex flex-col overflow-hidden bg-[#1a2438] p-2">
              <AnalysisItemSmall
                analysis={analysis}
                isSelected={false}
                onClick={() => {}}
              />
            </div>
          </div>
        </div>
      );
    }

    return null;
  };

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
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
      {renderModal()}
    </div>
  );
};

export default ProjectView;
