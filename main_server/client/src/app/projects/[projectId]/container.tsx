'use client';

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import EntitySidebar from "@/app/projects/[projectId]/_components/entity-sidebar/Sidebar";
import Chatbot from "@/app/projects/[projectId]/_components/chat/Chatbot";
import UserHeader from "@/components/headers/UserHeader";
import EntityRelationshipDiagram from "@/app/projects/[projectId]/_components/erd/EntityRelationshipDiagram";
import TabView from "@/app/projects/[projectId]/_components/tab-view/TabView";
import { useProject } from "@/hooks/useProject";
import { useTabContext } from "@/hooks/useTabContext";
import FileInfoModal from "@/components/info-modals/FileInfoModal";
import DatasetInfoModal from "@/components/info-modals/DatasetInfoModal";
import PipelineInfoModal from "@/components/info-modals/PipelineInfoModal";
import ModelInfoModal from "@/components/info-modals/ModelInfoModal";
import AnalysisItem from "@/components/info-modals/analysis/AnalysisItem";
import { UUID } from "crypto";

interface DashboardProps {
  session: Session;
  projectId: UUID;
}

function DashboardContent({ projectId }: { projectId: UUID }) {
  const { project } = useProject(projectId);
  const { openTabs, activeTabKey, closeTabByKey } = useTabContext(projectId);
  
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

  // Find the active tab
  const activeTab = openTabs.find(tab => tab.key === activeTabKey);

  // Render content based on active tab type
  let mainContent: React.ReactNode = null;
  
  if (activeTab?.type === 'project') {
    mainContent = <EntityRelationshipDiagram projectId={projectId} />;
  } else if (activeTab?.type === 'data_source') {
    mainContent = (
      <FileInfoModal
        dataSourceId={activeTab.id as UUID}
        onClose={() => closeTabByKey(activeTab.key)}
      />
    );
  } else if (activeTab?.type === 'dataset') {
    mainContent = (
      <DatasetInfoModal
        datasetId={activeTab.id as UUID}
        onClose={() => closeTabByKey(activeTab.key)}
        projectId={projectId}
      />
    );
  } else if (activeTab?.type === 'analysis') {
    mainContent = (
      <AnalysisItem
        analysisObjectId={activeTab.id as UUID}
        projectId={projectId}
        onClose={() => closeTabByKey(activeTab.key)}
      />
    );
  } else if (activeTab?.type === 'pipeline') {
    mainContent = (
      <PipelineInfoModal
        pipelineId={activeTab.id as UUID}
        onClose={() => closeTabByKey(activeTab.key)}
      />
    );
  } else if (activeTab?.type === 'model_entity') {
    mainContent = (
      <ModelInfoModal
        modelEntityId={activeTab.id as UUID}
        onClose={() => closeTabByKey(activeTab.key)}
        projectId={projectId}
      />
    );
  }

  // If a project is selected, show the main dashboard
  return (
    <div className="flex flex-col h-full bg-white">
      <UserHeader projectId={projectId}  />
      <div className="flex flex-1 h-[calc(100vh-3rem)]">
        <EntitySidebar projectId={projectId} />
        <main className="flex-1 min-w-0 overflow-hidden bg-white">
          <div className="flex flex-col h-full w-full">
            <TabView projectId={projectId} />
            <div className="flex-1 overflow-auto bg-gray-950">
              {mainContent}
            </div>
          </div>
        </main>
        <div className="w-[400px] shrink-0">
          <Chatbot projectId={projectId} />
        </div>
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