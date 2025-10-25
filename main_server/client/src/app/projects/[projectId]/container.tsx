'use client';

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import EntitySidebar from "@/app/projects/[projectId]/_components/entity-sidebar/Sidebar";
import Chatbot from "@/app/projects/[projectId]/_components/chat/Chatbot";
import UserHeader from "@/components/headers/UserHeader";
import EntityRelationshipDiagram from "@/app/projects/[projectId]/_components/erd/EntityRelationshipDiagram";
import TabView from "@/app/projects/[projectId]/_components/tab-view/TabView";
import { useProject } from "@/hooks/useProject";
import { useTabs } from "@/hooks/useTabs";
import FileInfoTab from "@/components/info-tabs/FileInfoTab";
import DatasetInfoTab from "@/components/info-tabs/DatasetInfoTab";
import PipelineInfoTab from "@/components/info-tabs/PipelineInfoTab";
import ModelInfoTab from "@/components/info-tabs/ModelInfoTab";
import AnalysisItem from "@/components/info-tabs/analysis/AnalysisItem";
import { UUID } from "crypto";

interface DashboardProps {
  session: Session;
  projectId: UUID;
}

function DashboardContent({ projectId }: { projectId: UUID }) {
  const { project } = useProject(projectId);
  const { openTabs, activeTabId, openTab, closeTab, selectTab } = useTabs();
  
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
    if (project.dataSources.some(ds => ds.dataSourceId === activeTabId)) return 'data_source';
    if (project.datasets.some(ds => ds.datasetId === activeTabId)) return 'dataset';
    if (project.analyses.some(a => a.analysisId === activeTabId)) return 'analysis';
    if (project.pipelines.some(p => p.pipelineId === activeTabId)) return 'pipeline';
    if (project.modelEntities.some(m => m.modelEntityId === activeTabId)) return 'model_entity';
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
        onClose={() => closeTab(activeTabId)}
      />
    );
  } else if (tabType === 'dataset' && activeTabId) {
    mainContent = (
      <DatasetInfoTab
        datasetId={activeTabId}
        onClose={() => closeTab(activeTabId)}
        projectId={projectId}
      />
    );
  } else if (tabType === 'analysis' && activeTabId) {
    mainContent = (
      <AnalysisItem
        analysisObjectId={activeTabId}
        projectId={projectId}
        onClose={() => closeTab(activeTabId)}
      />
    );
  } else if (tabType === 'pipeline' && activeTabId) {
    mainContent = (
      <PipelineInfoTab
        pipelineId={activeTabId}
        onClose={() => closeTab(activeTabId)}
        projectId={projectId}
      />
    );
  } else if (tabType === 'model_entity' && activeTabId) {
    mainContent = (
      <ModelInfoTab
        modelEntityId={activeTabId}
        onClose={() => closeTab(activeTabId)}
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
        
        <EntitySidebar projectId={projectId} />
        
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