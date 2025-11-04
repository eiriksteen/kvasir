'use client';

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import EntitySidebar from "@/app/projects/[projectId]/_components/entity-sidebar/Sidebar";
import Chatbot from "@/app/projects/[projectId]/_components/chat/Chatbot";
import UserHeader from "@/components/headers/UserHeader";
import EntityRelationshipDiagram from "@/app/projects/[projectId]/_components/erd/EntityRelationshipDiagram";
import TabView from "@/app/projects/[projectId]/_components/tab-view/TabView";
import { useProject } from "@/hooks/useProject";
import { useExtraction } from "@/hooks/useExtraction";
import { useTabs } from "@/hooks/useTabs";
import FileInfoTab from "@/components/info-tabs/FileInfoTab";
import DatasetInfoTab from "@/components/info-tabs/DatasetInfoTab";
import PipelineInfoTab from "@/components/info-tabs/PipelineInfoTab";
import ModelInfoTab from "@/components/info-tabs/ModelInfoTab";
import AnalysisItem from "@/components/info-tabs/analysis/AnalysisItem";
import { UUID } from "crypto";
import { RefreshCw } from "lucide-react";
import { useState, useCallback } from "react";

interface DashboardProps {
  session: Session;
  projectId: UUID;
}

function DashboardContent({ projectId }: { projectId: UUID }) {
  const { project } = useProject(projectId);
  const { openTabs, activeTabId, openTab, closeTab, closeTabToProject, selectTab } = useTabs();
  const { runExtraction } = useExtraction();
  const [isScanning, setIsScanning] = useState(false);

  const handleScanCodebase = useCallback(async () => {
    setIsScanning(true);
    try {
      await runExtraction({
        projectId,
        promptContent: "Scan the codebase to update the project graph. Identify and add any new data sources, datasets, pipelines, models, or analyses that exist in the code but are not yet reflected in the project graph. Remove any entities that no longer exist in the codebase. Ensure the graph accurately represents the current state of the project.",
      });
    } catch (error) {
      console.error('Failed to run extraction:', error);
    } finally {
      setIsScanning(false);
    }
  }, [projectId, runExtraction]);
  
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

  // Determine tab type based on activeTabId
  const getTabType = () => {
    if (activeTabId === null) return 'project';
    if (project.graph.dataSources.some(ds => ds.id === activeTabId)) return 'data_source';
    if (project.graph.datasets.some(ds => ds.id === activeTabId)) return 'dataset';
    if (project.graph.analyses.some(a => a.id === activeTabId)) return 'analysis';
    if (project.graph.pipelines.some(p => p.id === activeTabId)) return 'pipeline';
    if (project.graph.modelEntities.some(m => m.id === activeTabId)) return 'model_entity';
    return 'project';
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
        dataSourceId={activeTabId}
        projectId={projectId}
        onClose={() => closeTabToProject()}
        onDelete={() => closeTab(activeTabId)}
      />
    );
  } else if (tabType === 'dataset' && activeTabId) {
    mainContent = (
      <DatasetInfoTab
        datasetId={activeTabId}
        onClose={() => closeTabToProject()}
        onDelete={() => closeTab(activeTabId)}
        projectId={projectId}
      />
    );
  } else if (tabType === 'analysis' && activeTabId) {
    mainContent = (
      <AnalysisItem
        analysisObjectId={activeTabId}
        projectId={projectId}
        onClose={() => closeTabToProject()}
      />
    );
  } else if (tabType === 'pipeline' && activeTabId) {
    const activeTab = openTabs.find(tab => tab.id === activeTabId);
    mainContent = (
      <PipelineInfoTab
        pipelineId={activeTabId}
        onClose={() => closeTabToProject()}
        onDelete={() => closeTab(activeTabId)}
        projectId={projectId}
        initialView={activeTab?.initialView}
      />
    );
  } else if (tabType === 'model_entity' && activeTabId) {
    mainContent = (
      <ModelInfoTab
        modelEntityId={activeTabId}
        onClose={() => closeTabToProject()}
        onDelete={() => closeTab(activeTabId)}
        projectId={projectId}
      />
    );
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
            {/* Sync Graph Button - square button positioned directly under project tab, only visible in project view */}
            {isProjectView && (
              <div className="absolute top-[84px] left-0 z-20 flex items-center pointer-events-auto">
                <div className="h-9 w-px" />
                <button
                  onClick={handleScanCodebase}
                  disabled={isScanning}
                  className="flex items-center justify-center px-3 h-9 bg-white border-r border-b border-gray-100 text-[#000034] hover:bg-gray-100 disabled:opacity-50 transition-colors"
                  title="Scan codebase to sync project graph"
                >
                  <RefreshCw size={14} className={`${isScanning ? 'animate-spin' : ''}`} />
                </button>
              </div>
            )}
            <div className={`flex-1 overflow-auto ${
              isProjectView ? 'bg-transparent pointer-events-none' : 'bg-gray-950'
            }`}>
              {mainContent}
            </div>
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