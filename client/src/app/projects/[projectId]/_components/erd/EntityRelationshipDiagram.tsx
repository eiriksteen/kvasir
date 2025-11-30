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
import BranchBox from '@/app/projects/[projectId]/_components/erd/BranchBox';
import { UUID } from 'crypto';
import ModelInstantiatedBox from '@/app/projects/[projectId]/_components/erd/ModelEntityBox';
import { computeBoxEdgeLocations } from '@/app/projects/[projectId]/_components/erd/computeBoxEdgeLocations';
import { useEntityGraph } from '@/hooks/useEntityGraph';
import { LeafNode, PipelineNode, BranchNode, EntityLinks } from '@/types/ontology/entity-graph';

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

const ModelEntityNodeWrapper = ({ data }: { data: { modelInstantiatedId: UUID; projectId: UUID; openTab: (id: UUID | null | string, closable?: boolean, initialView?: 'overview' | 'code' | 'runs', filePath?: string) => void } }) => (
  <>
    <ModelInstantiatedBox
      modelInstantiatedId={data.modelInstantiatedId}
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

const BranchNodeWrapper = ({ data }: { data: { branchNode: BranchNode; projectId: UUID } }) => (
  <>
    <BranchBox
      branchNode={data.branchNode}
    />
    <Handle type="target" position={Position.Top} style={{ background: '#000000', left: 'calc(50% - 8px)' }} id="top-target" />
    <Handle type="source" position={Position.Top} style={{ background: '#000000', left: 'calc(50% + 8px)' }} id="top-source" />
    <Handle type="target" position={Position.Right} style={{ background: '#000000', top: 'calc(50% - 8px)' }} id="right-target" />
    <Handle type="source" position={Position.Right} style={{ background: '#000000', top: 'calc(50% + 8px)' }} id="right-source" />
    <Handle type="target" position={Position.Bottom} style={{ background: '#000000', left: 'calc(50% + 8px)' }} id="bottom-target" />
    <Handle type="source" position={Position.Bottom} style={{ background: '#000000', left: 'calc(50% - 8px)' }} id="bottom-source" />
    <Handle type="target" position={Position.Left} style={{ background: '#000000', top: 'calc(50% + 8px)' }} id="left-target" />
    <Handle type="source" position={Position.Left} style={{ background: '#000000', top: 'calc(50% - 8px)' }} id="left-source" />
  </>
);

const nodeTypes = {
  dataset: DatasetNodeWrapper,
  analysis: AnalysisNodeWrapper,
  dataSource: DataSourceNodeWrapper,
  pipeline: PipelineNodeWrapper,
  modelInstantiated: ModelEntityNodeWrapper,
  branch: BranchNodeWrapper,
};

const edgeTypes: EdgeTypes = {
  "custom-edge": TransportEdge
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
      case 'modelInstantiated':
        return '#491A32'; // Model entity color
      case 'branch':
        return '#000000'; // Branch color (black)
      default:
        return '#0E4F70'; // Default dataset color
    }
  }, []);

  const { entityGraph, triggerUpdateNodePosition } = useEntityGraph(projectId);
  const { project, triggerUpdateProjectViewPort } = useProject(projectId);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const { setViewport } = useReactFlow();

  useOnViewportChange({
    onEnd: (viewport: Viewport) => {
      triggerUpdateProjectViewPort({ projectId: projectId, viewPortX: viewport.x, viewPortY: viewport.y, zoom: viewport.zoom });
    }
  });

  useEffect(() => {
    if (project?.viewPortX && project?.viewPortY && project?.viewPortZoom) {

      setViewport({
        x: project.viewPortX,
        y: project.viewPortY,
        zoom: project.viewPortZoom,
      });

    }
  }, [project?.viewPortX, project?.viewPortY, project?.viewPortZoom, setViewport]);

  // Memoize nodes
  const memoizedNodes = useMemo(() => {
    if (!entityGraph) {
      return [];
    }

    const nodes: Node[] = [];

    // Add data source nodes
    entityGraph.dataSources.forEach((ds) => {
      if (ds.nodeType === 'branch') {
        const branchNode = ds as BranchNode;
        nodes.push({
          id: branchNode.id,
          type: 'branch',
          position: { x: branchNode.xPosition, y: branchNode.yPosition },
          data: {
            branchNode: branchNode,
            projectId: projectId, 
          },
        });
      } else {
        const leafNode = ds as LeafNode;
        nodes.push({
          id: leafNode.id,
          type: 'dataSource',
          position: { x: leafNode.xPosition, y: leafNode.yPosition },
          data: {
            dataSourceId: leafNode.entityId,
            projectId: projectId,
            openTab,
          },
        });
      }
    });

    // Add dataset nodes
    entityGraph.datasets.forEach((d) => {
      if (d.nodeType === 'branch') {
        const branchNode = d as BranchNode;
        nodes.push({
          id: branchNode.id,
          type: 'branch',
          position: { x: branchNode.xPosition, y: branchNode.yPosition },
          data: {
            branchNode: branchNode,
            projectId: projectId, 
          },
        });
      } else {
        const leafNode = d as LeafNode;
        nodes.push({
          id: leafNode.id,
          type: 'dataset',
          position: { x: leafNode.xPosition, y: leafNode.yPosition },
          data: {
            datasetId: leafNode.entityId,
            projectId: projectId,
            openTab,
          },
        });
      }
    });

    // Add pipeline nodes
    entityGraph.pipelines.forEach((p) => {
      if (p.nodeType === 'branch') {
        const branchNode = p as BranchNode;
        nodes.push({
          id: branchNode.id,
          type: 'branch',
          position: { x: branchNode.xPosition, y: branchNode.yPosition },
          data: {
            branchNode: branchNode,
            projectId: projectId,
          },
        });
      } else {
        const pipelineNode = p as PipelineNode;
        nodes.push({
          id: pipelineNode.id,
          type: 'pipeline',
          position: { x: pipelineNode.xPosition, y: pipelineNode.yPosition },
          data: {
            pipelineId: pipelineNode.entityId,
            projectId: projectId,
            openTab,
          },
        });
      }
    });

    // Add analysis nodes
    entityGraph.analyses.forEach((a) => {
      if (a.nodeType === 'branch') {
        const branchNode = a as BranchNode;
        nodes.push({
          id: branchNode.id,
          type: 'branch',
          position: { x: branchNode.xPosition, y: branchNode.yPosition },
          data: {
            branchNode: branchNode,
            projectId: projectId,
          },
        });
      } else {
        const leafNode = a as LeafNode;
        nodes.push({
          id: leafNode.id,
          type: 'analysis',
          position: { x: leafNode.xPosition, y: leafNode.yPosition },
          data: {
            analysisId: leafNode.entityId,
            projectId: projectId,
            openTab,
          },
        });
      }
    });

    // Add model entity nodes
    entityGraph.modelsInstantiated.forEach((me) => {
      if (me.nodeType === 'branch') {
        const branchNode = me as BranchNode;
        nodes.push({
          id: branchNode.id,
          type: 'branch',
          position: { x: branchNode.xPosition, y: branchNode.yPosition },
          data: {
            branchNode: branchNode,
            projectId: projectId, 
          },
        });
      } else {
        const leafNode = me as LeafNode;
        nodes.push({
          id: leafNode.id,
          type: 'modelInstantiated',
          position: { x: leafNode.xPosition, y: leafNode.yPosition },
          data: {
            modelInstantiatedId: leafNode.entityId,
            projectId: projectId,
            openTab,
          },
        });
      }
    });

    return nodes;

  }, [entityGraph, projectId, openTab]);

  // Memoize edges - uses current node positions from state for live updates during dragging
  const memoizedEdges = useMemo(() => {
    if (!entityGraph || nodes.length === 0) {
      return [];
    }

    // Helper to recursively collect all leaf nodes from a branch node
    const collectLeafNodes = (node: LeafNode | PipelineNode | BranchNode): (LeafNode | PipelineNode)[] => {
      if (node.nodeType === 'leaf') {
        return [node];
      }
      if (node.nodeType === 'branch') {
        const branchNode = node as BranchNode;
        const leaves: (LeafNode | PipelineNode)[] = [];
        for (const child of branchNode.children) {
          leaves.push(...collectLeafNodes(child));
        }
        return leaves;
      }
      return [];
    };

    // Helper to compute branch node edges from children
    const computeBranchEdges = (branchNode: BranchNode): { fromEntities: EntityLinks; toEntities: EntityLinks } => {
      const fromEntities: EntityLinks = {
        dataSources: [],
        datasets: [],
        analyses: [],
        pipelines: [],
        modelsInstantiated: [],
      };
      const toEntities: EntityLinks = {
        dataSources: [],
        datasets: [],
        analyses: [],
        pipelines: [],
        modelsInstantiated: [],
      };

      const leafNodes = collectLeafNodes(branchNode);
      
      for (const leaf of leafNodes) {
        // Handle pipeline nodes separately - they don't have toEntities, only runs do
        if (leaf.nodeType === 'leaf' && 'runs' in leaf) {
          const pipelineNode = leaf as PipelineNode;
          // Pipeline's input edges (fromEntities)
          fromEntities.dataSources.push(...pipelineNode.fromEntities.dataSources);
          fromEntities.datasets.push(...pipelineNode.fromEntities.datasets);
          fromEntities.analyses.push(...pipelineNode.fromEntities.analyses);
          fromEntities.pipelines.push(...pipelineNode.fromEntities.pipelines);
          fromEntities.modelsInstantiated.push(...pipelineNode.fromEntities.modelsInstantiated);

          // Pipeline runs' output edges (toEntities)
          for (const run of pipelineNode.runs) {
            toEntities.dataSources.push(...run.toEntities.dataSources);
            toEntities.datasets.push(...run.toEntities.datasets);
            toEntities.analyses.push(...run.toEntities.analyses);
            toEntities.pipelines.push(...run.toEntities.pipelines);
            toEntities.modelsInstantiated.push(...run.toEntities.modelsInstantiated);
          }
        } else {
          // Regular leaf nodes have both fromEntities and toEntities
          const leafNode = leaf as LeafNode;
          // Union of all fromEntities (edges coming into children)
          fromEntities.dataSources.push(...leafNode.fromEntities.dataSources);
          fromEntities.datasets.push(...leafNode.fromEntities.datasets);
          fromEntities.analyses.push(...leafNode.fromEntities.analyses);
          fromEntities.pipelines.push(...leafNode.fromEntities.pipelines);
          fromEntities.modelsInstantiated.push(...leafNode.fromEntities.modelsInstantiated);

          // Union of all toEntities (edges going out from children)
          toEntities.dataSources.push(...leafNode.toEntities.dataSources);
          toEntities.datasets.push(...leafNode.toEntities.datasets);
          toEntities.analyses.push(...leafNode.toEntities.analyses);
          toEntities.pipelines.push(...leafNode.toEntities.pipelines);
          toEntities.modelsInstantiated.push(...leafNode.toEntities.modelsInstantiated);
        }
      }

      // Remove duplicates
      const dedupe = (arr: UUID[]): UUID[] => Array.from(new Set(arr));
      return {
        fromEntities: {
          dataSources: dedupe(fromEntities.dataSources),
          datasets: dedupe(fromEntities.datasets),
          analyses: dedupe(fromEntities.analyses),
          pipelines: dedupe(fromEntities.pipelines),
          modelsInstantiated: dedupe(fromEntities.modelsInstantiated),
        },
        toEntities: {
          dataSources: dedupe(toEntities.dataSources),
          datasets: dedupe(toEntities.datasets),
          analyses: dedupe(toEntities.analyses),
          pipelines: dedupe(toEntities.pipelines),
          modelsInstantiated: dedupe(toEntities.modelsInstantiated),
        },
      };
    };

    // Build entity ID to node ID mapping for leaf nodes
    const entityIdToNodeId = new Map<UUID, UUID>();
    // Build node ID to root node ID mapping - maps child nodes to their root branch node shown in ERD
    const nodeIdToRootNodeId = new Map<UUID, UUID>();
    
    // Helper to recursively add nodes to maps and build root node mapping
    const addNodeToMaps = (node: LeafNode | PipelineNode | BranchNode, rootNodeId: UUID | null = null) => {
      // The root node ID is the node itself if it's a top-level node, or the parent branch if nested
      const currentRootNodeId = rootNodeId || node.id;
      
      if (node.nodeType === 'leaf') {
        const leafNode = node as LeafNode;
        entityIdToNodeId.set(leafNode.entityId, leafNode.id);
        // Map this leaf node to its root node (or itself if top-level)
        nodeIdToRootNodeId.set(leafNode.id, currentRootNodeId);
        
        if ('runs' in leafNode) {
          const pipelineNode = leafNode as PipelineNode;
          pipelineNode.runs.forEach(run => {
            entityIdToNodeId.set(run.entityId, run.id);
            // Pipeline runs are children, so map to root
            nodeIdToRootNodeId.set(run.id, currentRootNodeId);
          });
        }
      } else if (node.nodeType === 'branch') {
        const branchNode = node as BranchNode;
        // Branch node maps to itself if it's the root, or to its parent root
        nodeIdToRootNodeId.set(branchNode.id, currentRootNodeId);
        // Children of this branch node map to this branch node (which is shown in ERD)
        branchNode.children.forEach(child => addNodeToMaps(child, branchNode.id));
      }
    };
    
    entityGraph.dataSources.forEach(node => addNodeToMaps(node));
    entityGraph.datasets.forEach(node => addNodeToMaps(node));
    entityGraph.pipelines.forEach(node => addNodeToMaps(node));
    entityGraph.analyses.forEach(node => addNodeToMaps(node));
    entityGraph.modelsInstantiated.forEach(node => addNodeToMaps(node));

    // Helper to get node position from current nodes state (updates during dragging)
    const getNodePosition = (nodeId: UUID): { xPosition: number, yPosition: number } | null => {
      const currentNode = nodes.find(n => n.id === nodeId);
      if (currentNode) {
        return { xPosition: currentNode.position.x, yPosition: currentNode.position.y };
      }
      return null;
    };

    // Helper to get root node ID from entity ID (redirects child nodes to their branch node)
    const getRootNodeIdFromEntityId = (entityId: UUID): UUID | null => {
      const nodeId = entityIdToNodeId.get(entityId);
      if (!nodeId) return null;
      // Get the root node ID (branch node if child, or node itself if top-level)
      return nodeIdToRootNodeId.get(nodeId) || nodeId;
    };

    // Helper to determine source type for edge color based on root node
    const getSourceTypeFromRootNode = (rootNodeId: UUID): 'dataSource' | 'dataset' | 'analysis' | 'pipeline' | 'modelInstantiated' | 'branch' => {
      // Check if it's a branch node by seeing if any node maps to it as root (and it's not itself)
      for (const [nodeId, rootId] of nodeIdToRootNodeId.entries()) {
        if (rootId === rootNodeId && nodeId !== rootNodeId) {
          return 'branch';
        }
      }
      // If it's a leaf node, determine type from the entity graph
      // For now, return 'branch' if we can't determine - this is just for edge color
      return 'branch';
    };

    // Generic edge creation helper - converts entity IDs or node IDs to root node IDs
    const createEdgeFromEntityIds = (
      fromId: UUID,
      toId: UUID
    ): Edge | null => {
      // Handle both entity IDs and node IDs (branch nodes use node IDs)
      const fromRootNodeId = nodeIdToRootNodeId.has(fromId)
        ? (nodeIdToRootNodeId.get(fromId) || fromId)
        : getRootNodeIdFromEntityId(fromId);
      const toRootNodeId = nodeIdToRootNodeId.has(toId)
        ? (nodeIdToRootNodeId.get(toId) || toId)
        : getRootNodeIdFromEntityId(toId);
      
      if (!fromRootNodeId || !toRootNodeId) return null;
      
      // Skip self-edges
      if (fromRootNodeId === toRootNodeId) return null;

      const sourcePos = getNodePosition(fromRootNodeId);
      const targetPos = getNodePosition(toRootNodeId);
      if (!sourcePos || !targetPos) return null;

      const sourceType = getSourceTypeFromRootNode(fromRootNodeId);
      const edgeLocation = computeBoxEdgeLocations(sourcePos, targetPos);
      return {
        id: String(`${fromRootNodeId}->${toRootNodeId}`),
        source: fromRootNodeId,
        target: toRootNodeId,
        type: 'default',
        animated: true,
        style: { stroke: getEdgeColor(sourceType), strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed },
        sourceHandle: edgeLocation.from,
        targetHandle: edgeLocation.to,
      } as Edge;
    };

    // Extract all edges from the graph - collect all entity ID pairs
    const edgePairs: Array<{ fromEntityId: UUID; toEntityId: UUID }> = [];
    
    // Helper to collect edges from a leaf node's toEntities
    const collectLeafNodeEdges = (leafNode: LeafNode) => {
      const addEdges = (toEntityIds: UUID[]) => {
        toEntityIds.forEach(toEntityId => {
          edgePairs.push({ fromEntityId: leafNode.entityId, toEntityId });
        });
      };
      
      addEdges(leafNode.toEntities.dataSources);
      addEdges(leafNode.toEntities.datasets);
      addEdges(leafNode.toEntities.analyses);
      addEdges(leafNode.toEntities.pipelines);
      addEdges(leafNode.toEntities.modelsInstantiated);
    };
    
    // Helper to collect edges from a leaf node's fromEntities (input edges)
    // Works for both LeafNode and PipelineNode (which both have fromEntities)
    const collectLeafNodeFromEdges = (node: LeafNode | PipelineNode) => {
      const addEdges = (fromEntityIds: UUID[]) => {
        fromEntityIds.forEach(fromEntityId => {
          edgePairs.push({ fromEntityId, toEntityId: node.entityId });
        });
      };
      
      addEdges(node.fromEntities.dataSources);
      addEdges(node.fromEntities.datasets);
      addEdges(node.fromEntities.analyses);
      addEdges(node.fromEntities.pipelines);
      addEdges(node.fromEntities.modelsInstantiated);
    };
    
    // Process all leaf nodes
    entityGraph.dataSources.forEach(node => {
      if (node.nodeType === 'leaf') {
        collectLeafNodeEdges(node as LeafNode);
      }
    });
    
    entityGraph.datasets.forEach(node => {
      if (node.nodeType === 'leaf') {
        collectLeafNodeEdges(node as LeafNode);
      }
    });
    
    entityGraph.analyses.forEach(node => {
      if (node.nodeType === 'leaf') {
        collectLeafNodeEdges(node as LeafNode);
      }
    });
    
    entityGraph.pipelines.forEach(node => {
      if (node.nodeType === 'leaf') {
        const pipelineNode = node as PipelineNode;
        // Process pipeline's input edges (fromEntities)
        collectLeafNodeFromEdges(pipelineNode);
        // Process pipeline runs' output edges (toEntities)
        pipelineNode.runs.forEach(run => {
          collectLeafNodeEdges(run);
        });
      }
    });
    
    entityGraph.modelsInstantiated.forEach(node => {
      if (node.nodeType === 'leaf') {
        collectLeafNodeEdges(node as LeafNode);
      }
    });
    
    // Process branch nodes - compute edges from children
    const processBranchNode = (branchNode: BranchNode) => {
      const branchEdges = computeBranchEdges(branchNode);
      
      const addEdgesFrom = (fromEntityIds: UUID[]) => {
        fromEntityIds.forEach(fromEntityId => {
          edgePairs.push({ fromEntityId, toEntityId: branchNode.id });
        });
      };
      
      const addEdgesTo = (toEntityIds: UUID[]) => {
        toEntityIds.forEach(toEntityId => {
          edgePairs.push({ fromEntityId: branchNode.id, toEntityId });
        });
      };
      
      // Input edges to branch node
      addEdgesFrom(branchEdges.fromEntities.dataSources);
      addEdgesFrom(branchEdges.fromEntities.datasets);
      addEdgesFrom(branchEdges.fromEntities.analyses);
      addEdgesFrom(branchEdges.fromEntities.pipelines);
      addEdgesFrom(branchEdges.fromEntities.modelsInstantiated);
      
      // Output edges from branch node
      addEdgesTo(branchEdges.toEntities.dataSources);
      addEdgesTo(branchEdges.toEntities.datasets);
      addEdgesTo(branchEdges.toEntities.analyses);
      addEdgesTo(branchEdges.toEntities.pipelines);
      addEdgesTo(branchEdges.toEntities.modelsInstantiated);
    };
    
    entityGraph.dataSources.forEach(node => {
      if (node.nodeType === 'branch') {
        processBranchNode(node as BranchNode);
      }
    });
    
    entityGraph.datasets.forEach(node => {
      if (node.nodeType === 'branch') {
        processBranchNode(node as BranchNode);
      }
    });
    
    entityGraph.analyses.forEach(node => {
      if (node.nodeType === 'branch') {
        processBranchNode(node as BranchNode);
      }
    });
    
    entityGraph.pipelines.forEach(node => {
      if (node.nodeType === 'branch') {
        processBranchNode(node as BranchNode);
      }
    });
    
    entityGraph.modelsInstantiated.forEach(node => {
      if (node.nodeType === 'branch') {
        processBranchNode(node as BranchNode);
      }
    });
    
    // Convert all edge pairs to edges using root node IDs
    const allEdges: Edge[] = [];
    for (const { fromEntityId, toEntityId } of edgePairs) {
      const edge = createEdgeFromEntityIds(fromEntityId, toEntityId);
      if (edge) allEdges.push(edge);
    }

    // Remove duplicate edges (same source and target)
    const edgeSet = new Set<string>();
    const uniqueEdges: Edge[] = [];
    for (const edge of allEdges) {
      const key = `${edge.source}->${edge.target}`;
      if (!edgeSet.has(key)) {
        edgeSet.add(key);
        uniqueEdges.push(edge);
      }
    }

    return uniqueEdges;
  }, [entityGraph, getEdgeColor, nodes]);

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
    if (!entityGraph || !node || !node.id) return;

    triggerUpdateNodePosition({
      nodeId: node.id as UUID,
      xPosition: node.position.x,
      yPosition: node.position.y,
    });
  }, [entityGraph, triggerUpdateNodePosition]);

  return (
    <div className="w-full h-full bg-white">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        minZoom={0.1}
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