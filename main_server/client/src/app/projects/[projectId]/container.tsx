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

interface DashboardProps {
  session: Session;
  projectId: UUID;
}

function DashboardContent({ projectId }: { projectId: UUID }) {
  const { project } = useProject(projectId);
  const { openTabs, activeTabId, openTab, closeTab, closeTabToProject, selectTab } = useTabs();
  const { runExtraction } = useExtraction();
  const { runs } = useRuns();
  const [isScanning, setIsScanning] = useState(false);

  // Check if any extraction runs are currently running in this project
  const hasRunningExtractionRuns = useMemo(() => {
    return runs.some(run => 
      run.type === 'extraction' && 
      run.status === 'running' && 
      run.projectId === projectId
    );
  }, [runs, projectId]);

  const handleScanCodebase = useCallback(async () => {
    setIsScanning(true);
    try {
      await runExtraction({
        projectId,
        promptContent: "Scan the codebase to update the project graph. Add any new entities, remove any no longer relevant, add new edges between entities, or remove any edges that are no longer relevant. Ensure the graph accurately represents the current state of the project. ",
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
    
    // Check if it's a code tab
    
    if (project.graph.dataSources.some(ds => ds.id === activeTabId)) return 'data_source';
    if (project.graph.datasets.some(ds => ds.id === activeTabId)) return 'dataset';
    if (project.graph.analyses.some(a => a.id === activeTabId)) return 'analysis';
    if (project.graph.pipelines.some(p => p.id === activeTabId)) return 'pipeline';
    if (project.graph.modelEntities.some(m => m.id === activeTabId)) return 'model_entity';
    else return 'code';
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
        projectId={projectId}
        onClose={() => closeTabToProject()}
        onDelete={() => closeTab(activeTabId)}
      />
    );
  } else if (tabType === 'dataset' && activeTabId) {
    mainContent = (
      <DatasetInfoTab
        datasetId={activeTabId as UUID}
        onClose={() => closeTabToProject()}
        onDelete={() => closeTab(activeTabId)}
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
        onDelete={() => closeTab(activeTabId)}
        projectId={projectId}
        initialView={activeTab?.initialView as 'overview' | 'runs' | undefined}
      />
    );
  } else if (tabType === 'model_entity' && activeTabId) {
    mainContent = (
      <ModelInfoTab
        modelEntityId={activeTabId as UUID}
        onClose={() => closeTabToProject()}
        onDelete={() => closeTab(activeTabId)}
        projectId={projectId}
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