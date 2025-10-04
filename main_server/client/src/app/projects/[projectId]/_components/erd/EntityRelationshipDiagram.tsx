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
import { FrontendNode } from '@/types/node';
import DatasetBox from '@/app/projects/[projectId]/_components/erd/DatasetBox';
import AnalysisBox from '@/app/projects/[projectId]/_components/erd/AnalysisBox';
import TransportEdge from '@/app/projects/[projectId]/_components/erd/TransportEdge';
import { useProjectDataSources } from '@/hooks/useDataSources';
import DataSourceBox from '@/app/projects/[projectId]/_components/erd/DataSourceBox';
import FileInfoModal from '@/components/info-modals/FileInfoModal';
import DatasetInfoModal from '@/components/info-modals/DatasetInfoModal';
import PipelineBox from '@/app/projects/[projectId]/_components/erd/PipelineBox';
import PipelineInfoModal from '@/components/info-modals/PipelineInfoModal';
import { UUID } from 'crypto';
import { ModelEntity } from '@/types/model';
import { useModelEntities } from '@/hooks/useModelEntities';
import ModelEntityBox from '@/app/projects/[projectId]/_components/erd/ModelEntityBox';
import ModelInfoModal from '@/components/info-modals/ModelInfoModal';
import { useProjectGraph } from '@/hooks/useProjectGraph';
import { useTabContext } from '@/hooks/useTabContext';
import TabView from '@/app/projects/[projectId]/_components/erd/TabView';
import AnalysisItem from '@/components/info-modals/analysis/AnalysisItem';

import { DataSource } from '@/types/data-sources';
import { Dataset } from '@/types/data-objects';
import { AnalysisObjectSmall } from '@/types/analysis';
import { Pipeline } from '@/types/pipeline';

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
const AnalysisNodeWrapper = ({ data }: { data: { analysis: AnalysisObjectSmall; onClick: () => void } }) => (
  <>
  <AnalysisBox
    analysis={data.analysis}
    onClick={data.onClick}
  />
  <Handle type="target" position={Position.Left} style={{ background: '#004806' }} />
  <Handle type="source" position={Position.Right} style={{ background: '#004806' }} />
  </>
);

const PipelineNodeWrapper = ({ data }: { data: { pipeline: Pipeline; onClick: () => void } }) => (
  <>
    <PipelineBox
      pipeline={data.pipeline}
      onClick={data.onClick}
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
  const { pipelines } = usePipelines(projectId);
  const { modelEntities } = useModelEntities(projectId);
  const { analysisObjects } = useAnalysis(projectId);
  const { projectGraph } = useProjectGraph(projectId);
  const { openTab, openTabs, activeTabKey, closeTabByKey, setProjectTabLabel } = useTabContext(projectId);
  
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  console.log(projectGraph);

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
          onClick: () => handleOpenTab({ type: 'data_source', id: dataSource.id, label: dataSource.name })
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
          onClick: () => handleOpenTab({ type: 'dataset', id: dataset.id, label: dataset.name })
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
          onClick: () => handleOpenTab({ type: 'pipeline', id: pipeline.id, label: pipeline.name })
        },
      } as Node;
    });

    const analysisNodes = frontendNodes.map((frontendNode: FrontendNode) => {
      const analysis = analysisObjects.analysisObjects.find(a => a.id === frontendNode.analysisId);
      if (!analysis) return null;
      return {
        id: frontendNode.id,
        type: 'analysis',
        position: { x: frontendNode.xPosition, y: frontendNode.yPosition },
        data: {
          label: analysis.name,
          id: frontendNode.analysisId,
          analysis: analysis,
          onClick: () => handleOpenTab({ type: 'analysis', id: analysis.id, label: analysis.name })
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
          onClick: () => handleOpenTab({ type: 'model_entity', id: modelEntity.id, label: modelEntity.name })
        },
      } as Node;
    });

    return [...datasetNodes.filter(Boolean), ...analysisNodes.filter(Boolean), ...dataSourceNodes.filter(Boolean), ...pipelineNodes.filter(Boolean), ...modelEntityNodes.filter(Boolean)] as Node[];

  }, [project, datasets, analysisObjects, frontendNodes, dataSources, pipelines, modelEntities, handleOpenTab]);

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

  // Tab content rendering
  let tabContent: React.ReactNode = null;
  const activeTab = openTabs.find(tab => tab.key === activeTabKey);
  
  if (activeTab?.type === 'project') {
    tabContent = (
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
  } 
  else if (activeTab?.type === 'data_source') {
    tabContent = (
      <FileInfoModal
        dataSourceId={activeTab.id as UUID}
        onClose={() => closeTabByKey(activeTab.key)}
      />
    );
  } 
  else if (activeTab?.type === 'dataset') {
    tabContent = (
      <DatasetInfoModal
        datasetId={activeTab.id as UUID}
        onClose={() => closeTabByKey(activeTab.key)}
        projectId={projectId}
      />
    );
  } 
  else if (activeTab?.type === 'analysis') {
    tabContent = (
      <AnalysisItem
        analysisObjectId={activeTab.id as UUID}
        projectId={projectId}
        onClose={() => closeTabByKey(activeTab.key)}
      />
    );
  } 
  else if (activeTab?.type === 'pipeline') {
    tabContent = (
      <PipelineInfoModal
        pipelineId={activeTab.id as UUID}
        onClose={() => closeTabByKey(activeTab.key)}
      />
    );
  } 
  else if (activeTab?.type === 'model_entity') {
    tabContent = (
      <ModelInfoModal
        modelEntityId={activeTab.id as UUID}
        onClose={() => closeTabByKey(activeTab.key)}
        projectId={projectId}
      />
    );
  }

  return (
    <div className="w-full h-screen flex flex-col pt-10">
      <TabView projectId={projectId}>
        {tabContent}
      </TabView>
    </div>
  );
};
