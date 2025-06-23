'use client';

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import OntologyBar from "@/components/OntologyBar";
import Chatbot from "@/components/Chatbot";
import UserHeader from "@/components/UserHeader";
import ProjectView from "@/components/ProjectView";
import { useProject } from "@/hooks/useProject";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
// import MainView from "@/components/MainView";

interface DashboardProps {
  session: Session;
}

function DashboardContent() {
  const { selectedProject } = useProject();
  const router = useRouter();
  
  // If no project is selected, redirect to project selection
  useEffect(() => {
    if (!selectedProject) {
      router.push('/select-project');
    }
  }, [selectedProject, router]);

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
      <UserHeader />
      <div className="flex flex-1 h-[calc(100vh-3rem)]">
        <OntologyBar />
        <main className="flex-1 min-w-0 overflow-hidden">
          <ProjectView />
        </main>
        <div className="w-[400px] shrink-0">
          <Chatbot />
        </div>
      </div>
    </div>
  );
}

export default function DashboardContainer({ session }: DashboardProps) {
  return (
    <SessionProvider session={session}>
      <DashboardContent />
    </SessionProvider>
  );
} 