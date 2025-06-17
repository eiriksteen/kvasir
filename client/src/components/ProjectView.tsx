import React, { useCallback, useState, useEffect } from 'react';
import {
    ReactFlow,
    Node,
    Edge,
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    addEdge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useProject } from '@/hooks/useProject';
import { useDatasets, useAnalysis } from '@/hooks';
import DataVisualizer from './DataVisualizer';
import AnalysisItemSmall from './analysis/AnalysisItem';
import { X } from 'lucide-react';

// Custom node types
const nodeTypes = {
  dataset: ({ data }: { data: { label: string; id: string; onClick: () => void } }) => (
    <div 
      className="px-4 py-2 shadow-md rounded-md bg-[#050a14] border-2 border-[#101827] cursor-pointer hover:bg-[#0a101c]"
      onClick={data.onClick}
    >
      <div className="flex items-center">
        <div className="rounded-full w-12 h-12 flex items-center justify-center bg-[#0e1a30]">
          <svg className="w-6 h-6 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
          </svg>
        </div>
        <div className="ml-2">
          <div className="text-lg font-bold text-white">{data.label}</div>
          <div className="text-blue-300">Dataset</div>
        </div>
      </div>
    </div>
  ),
  analysis: ({ data }: { data: { label: string; id: string; onClick: () => void } }) => (
    <div 
      className="px-4 py-2 shadow-md rounded-md bg-[#1a1625]/80 border-2 border-[#271a30] cursor-pointer hover:bg-[#2a1c30]"
      onClick={data.onClick}
    >
      <div className="flex items-center">
        <div className="rounded-full w-12 h-12 flex items-center justify-center bg-[#2a1c30]">
          <svg className="w-6 h-6 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <div className="ml-2">
          <div className="text-lg font-bold text-white">{data.label}</div>
          <div className="text-purple-300">Analysis</div>
        </div>
      </div>
    </div>
  ),
};

const ProjectView: React.FC = () => {
  const { selectedProject } = useProject();
  const { datasets } = useDatasets();
  const { analysisJobResults } = useAnalysis();
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState<string | null>(null);

  // Create nodes based on selected project's datasets and analyses
  const initialNodes: Node[] = React.useMemo(() => {
    if (!selectedProject || !datasets?.timeSeries || !analysisJobResults?.analysesJobResults) {
      return [];
    }

    const datasetNodes = selectedProject.datasetIds.map((datasetId: string, index: number) => {
      const dataset = datasets.timeSeries.find(d => d.id === datasetId);
      if (!dataset) return null;

      return {
        id: datasetId,
        type: 'dataset',
        position: { x: 250, y: 100 + (index * 150) },
        data: { 
          label: dataset.name,
          id: datasetId,
          onClick: () => setSelectedDataset(datasetId)
        },
      };
    }).filter(Boolean);

    const analysisNodes = selectedProject.analysisIds.map((analysisId: string, index: number) => {
      const analysis = analysisJobResults.analysesJobResults.find(a => a.jobId === analysisId);
      if (!analysis) return null;

      return {
        id: analysisId,
        type: 'analysis',
        position: { x: 500, y: 100 + (index * 150) },
        data: { 
          label: analysis.name || `Analysis ${index + 1}`,
          id: analysisId,
          onClick: () => setSelectedAnalysis(analysisId)
        },
      };
    }).filter(Boolean);

    return [...datasetNodes, ...analysisNodes];
  }, [selectedProject, datasets, analysisJobResults]);

  const initialEdges: Edge[] = React.useMemo(() => {
    if (!selectedProject || !analysisJobResults?.analysesJobResults) return [];
    
    return analysisJobResults.analysesJobResults
      .filter(analysis => selectedProject.analysisIds.includes(analysis.jobId))
      .flatMap(analysis => 
        analysis.datasetIds.map(datasetId => ({
          id: `e${datasetId}-${analysis.jobId}`,
          source: datasetId,
          target: analysis.jobId,
        }))
      );
  }, [selectedProject, analysisJobResults]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes when initialNodes changes
  useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes, setNodes]);

  // Update edges when initialEdges changes
  useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  const onConnect = useCallback((params: any) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

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
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background />
        {/* <Controls />
        <MiniMap /> */}
      </ReactFlow>
      {renderModal()}
    </div>
  );
};

export default ProjectView;
