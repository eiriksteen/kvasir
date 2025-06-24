'use client';

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import OntologyBar from "@/components/OntologyBar";
import Chatbot from "@/components/chat/Chatbot";
import UserHeader from "@/components/headers/UserHeader";
import ProjectView from "@/components/project/ProjectView";
import { useProject } from "@/hooks/useProject";
// import MainView from "@/components/MainView";

interface DashboardProps {
  session: Session;
  projectId: string;
}

function DashboardContent({ projectId }: { projectId: string }) {
  const { selectedProject } = useProject(projectId);
  
  // If no project is selected, show loading or return null
  if (!selectedProject) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zinc-950">
        <div className="text-center">
          <div className="w-6 h-6 animate-spin text-zinc-400 mx-auto mb-3 border-2 border-zinc-600 border-t-zinc-400 rounded-full"></div>
          <p className="text-zinc-400 text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  // If a project is selected, show the main dashboard
  return (
    <div className="flex flex-col h-full bg-zinc-950">
      <UserHeader projectId={projectId}  />
      <div className="flex flex-1 h-[calc(100vh-3rem)]">
        <OntologyBar projectId={projectId} />
        <main className="flex-1 min-w-0 overflow-hidden">
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
    <SessionProvider session={session}>
      <DashboardContent projectId={projectId} />
    </SessionProvider>
  );
} 