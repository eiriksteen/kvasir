'use client';

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import EntitySidebar from "@/app/projects/[projectId]/_components/entity-sidebar/Sidebar";
import Chatbot from "@/app/projects/[projectId]/_components/chat/Chatbot";
import UserHeader from "@/components/headers/UserHeader";
import ProjectView from "@/app/projects/[projectId]/_components/erd/EntityRelationshipDiagram";
import { useProject } from "@/hooks/useProject";
// import MainView from "@/components/MainView";
import { UUID } from "crypto";

interface DashboardProps {
  session: Session;
  projectId: UUID;
}

function DashboardContent({ projectId }: { projectId: UUID }) {
  const { project } = useProject(projectId);
  
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

  // If a project is selected, show the main dashboard
  return (
    <div className="flex flex-col h-full bg-white">
      <UserHeader projectId={projectId}  />
      <div className="flex flex-1 h-[calc(100vh-3rem)]">
        <EntitySidebar projectId={projectId} />
        <main className="flex-1 min-w-0 overflow-hidden bg-white">
          <ProjectView projectId={projectId} />
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
      <DashboardContent projectId={projectId} />
    </SessionProvider>
  );
} 