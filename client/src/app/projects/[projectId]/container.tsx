'use client';

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import EntitySidebar from "@/app/projects/[projectId]/_components/entity-sidebar/Sidebar";
import Chatbot from "@/app/projects/[projectId]/_components/chat/Chatbot";
import UserHeader from "@/components/headers/UserHeader";
import EntityRelationshipDiagram from "@/app/projects/[projectId]/_components/erd/EntityRelationshipDiagram";
import TabView from "@/app/projects/[projectId]/_components/tab-view/TabView";
import { useProject } from "@/hooks/useProject";
import { useOntology } from "@/hooks/useOntology";
import { useTabs } from "@/hooks/useTabs";
import { useRuns } from "@/hooks/useRuns";
import FileInfoTab from "@/components/info-tabs/FileInfoTab";
import DatasetInfoTab from "@/components/info-tabs/DatasetInfoTab";
import PipelineInfoTab from "@/components/info-tabs/PipelineInfoTab";
import ModelInfoTab from "@/components/info-tabs/ModelInfoTab";
import AnalysisItem from "@/components/info-tabs/analysis/AnalysisItem";
import CodeInfoTab from "@/components/info-tabs/CodeInfoTab";
import { UUID } from "crypto";
import { RefreshCw } from "lucide-react";
import { useState, useCallback, useMemo } from "react";
import { LeafNode, PipelineNode, BranchNode } from "@/types/ontology/entity-graph";

interface DashboardProps {
  session: Session;
  projectId: UUID;
}

function DashboardContent({ projectId }: { projectId: UUID }) {
  const { project } = useProject(projectId);
  const { openTabs, activeTabId, openTab, closeTab, closeTabToProject, selectTab } = useTabs();
  const { runExtraction, entityGraph } = useOntology(projectId);
  const { runs } = useRuns(projectId);
  const [isScanning, setIsScanning] = useState(false);



  // Check if any extraction runs are currently running in this project
  const hasRunningExtractionRuns = useMemo(() => {
    return runs.some(run => 
      run.type === 'extraction' && 
      run.status === 'running'
    );
  }, [runs]);

  const handleScanCodebase = useCallback(async () => {
    setIsScanning(true);
    try {
      await runExtraction();
    } catch (error) {
      console.error('Failed to run extraction:', error);
    } finally {
      setIsScanning(false);
    }
  }, [runExtraction]);
  
  // If no project is selected, show loading or return null
  if (!project) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="text-center">
          <div className="w-6 h-6 animate-spin text-zinc-400 mx-auto mb-3 border-2 border-zinc-600 border-t-zinc-400 rounded-full"></div>
          <p className="text-zinc-400 text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  // Helper to recursively find a leaf node by entityId
  const findLeafNodeByEntityId = (nodes: (LeafNode | PipelineNode | BranchNode)[], entityId: UUID): LeafNode | PipelineNode | null => {
    for (const node of nodes) {
      if (node.nodeType === 'leaf' || node.nodeType === 'branch') {
        if (node.nodeType === 'leaf' && (node as LeafNode | PipelineNode).entityId === entityId) {
          return node as LeafNode | PipelineNode;
        }
        if (node.nodeType === 'branch') {
          const found = findLeafNodeByEntityId((node as BranchNode).children, entityId);
          if (found) return found;
        }
      }
    }
    return null;
  };

  const getTabType = () => {
    if (activeTabId === null) return 'project';
    
    // Search recursively through all entity types
    if (entityGraph?.dataSources) {
      const found = findLeafNodeByEntityId(entityGraph.dataSources, activeTabId as UUID);
      if (found && found.entityType === 'data_source') return 'data_source';
    }
    
    if (entityGraph?.datasets) {
      const found = findLeafNodeByEntityId(entityGraph.datasets, activeTabId as UUID);
      if (found && found.entityType === 'dataset') return 'dataset';
    }
    
    if (entityGraph?.analyses) {
      const found = findLeafNodeByEntityId(entityGraph.analyses, activeTabId as UUID);
      if (found && found.entityType === 'analysis') return 'analysis';
    }
    
    if (entityGraph?.pipelines) {
      const found = findLeafNodeByEntityId(entityGraph.pipelines, activeTabId as UUID);
      if (found && found.entityType === 'pipeline') return 'pipeline';
    }
    
    if (entityGraph?.modelsInstantiated) {
      const found = findLeafNodeByEntityId(entityGraph.modelsInstantiated, activeTabId as UUID);
      if (found && found.entityType === 'model_instantiated') return 'model_instantiated';
    }
    
    return 'code';
  };

  const tabType = getTabType();
  const isProjectView = tabType === 'project';

  // Render content based on active tab type
  let mainContent: React.ReactNode = null;
  
  if (isProjectView) {
    // ERD is handled by absolute positioning, so no content needed here
    mainContent = null;
  } else if (tabType === 'data_source' && activeTabId) {
    mainContent = (
      <FileInfoTab
        dataSourceId={activeTabId as UUID}
        onClose={() => closeTabToProject()}
      />
    );
  } else if (tabType === 'dataset' && activeTabId) {
    mainContent = (
      <DatasetInfoTab
        datasetId={activeTabId as UUID}
        onClose={() => closeTabToProject()}
        projectId={projectId}
      />
    );
  } else if (tabType === 'analysis' && activeTabId) {
    mainContent = (
      <AnalysisItem
        analysisObjectId={activeTabId as UUID}
        projectId={projectId}
        onClose={() => closeTabToProject()}
      />
    );
  } else if (tabType === 'pipeline' && activeTabId) {
    const activeTab = openTabs.find(tab => tab.id === activeTabId);
    mainContent = (
      <PipelineInfoTab
        pipelineId={activeTabId as UUID}
        onClose={() => closeTabToProject()}
        initialView={activeTab?.initialView as 'overview' | 'runs' | undefined}
      />
    );
  } else if (tabType === 'model_instantiated' && activeTabId) {
    mainContent = (
      <ModelInfoTab
        modelInstantiatedId={activeTabId as UUID}
        onClose={() => closeTabToProject()}
      />
    );
  } else if (tabType === 'code' && activeTabId) {
    const activeTab = openTabs.find(tab => tab.id === activeTabId);
    if (activeTab?.filePath) {
      mainContent = (
        <CodeInfoTab
          projectId={projectId}
          filePath={activeTab.filePath}
          onClose={() => closeTabToProject()}
        />
      );
    }
  }

  // This is ugly, but turns out to be really hard to let the ERD be fixed while the rest is adaptive. 
  // It works, but may be worth a revisit. 
  return (
    <div className="flex flex-col h-full bg-white relative">
      <UserHeader projectId={projectId}  />
      <div className="flex flex-1 h-[calc(100vh-3rem)] relative">
        {/* ERD positioned absolutely to remain fixed */}
        {isProjectView && (
          <div className="absolute inset-0 z-0">
            <EntityRelationshipDiagram projectId={projectId} openTab={openTab} />
          </div>
        )}
        
        <EntitySidebar projectId={projectId} openTab={openTab} />
        
        <main className={`flex-1 min-w-0 overflow-hidden relative z-10 ${
          isProjectView ? 'bg-transparent pointer-events-none' : 'bg-white'
        }`}>
          <div className="flex flex-col h-full w-full">
            <div className={isProjectView ? 'pointer-events-auto' : ''}>
              <TabView 
                projectId={projectId}
                openTabs={openTabs}
                activeTabId={activeTabId}
                closeTab={closeTab}
                selectTab={selectTab}
              />
            </div>
            <div className={`flex-1 overflow-auto ${
              isProjectView ? 'bg-transparent pointer-events-none' : ''
            }`}>
              {mainContent}
            </div>
            {/* Sync Graph Button - positioned at bottom left, only visible in project view */}
            {isProjectView && (
              <div className="absolute bottom-2 left-2 z-20 pointer-events-auto">
                <button
                  onClick={handleScanCodebase}
                  disabled={isScanning || hasRunningExtractionRuns}
                  className="flex items-center justify-center p-2 bg-white border border-gray-300 rounded-lg text-[#000034] hover:bg-gray-50 disabled:opacity-50 transition-colors shadow-sm"
                  title="Scan codebase to sync project graph"
                >
                  <RefreshCw size={16} className={`${isScanning || hasRunningExtractionRuns ? 'animate-spin' : ''}`} />
                </button>
              </div>
            )}
          </div>
        </main>
        
        <Chatbot projectId={projectId} />
      </div>
    </div>
  );
}

export default function ProjectContainer({ projectId, session }: DashboardProps) {
  return (
    <SessionProvider session={session} basePath="/next-api/api/auth">
      <div className="h-screen">
        <DashboardContent projectId={projectId} />
      </div>
    </SessionProvider>
  );
} 