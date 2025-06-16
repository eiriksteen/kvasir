'use client';

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import OntologyBar from "@/components/OntologyBar";
import Chatbot from "@/components/Chatbot";
import UserHeader from "@/components/UserHeader";
import DataVisualizer from "@/components/data-visualization/DataVisualizer";
import ProjectView from "@/components/ProjectView";
// import MainView from "@/components/MainView";

interface DashboardProps {
  session: Session;
}

export default function DashboardContainer({ session }: DashboardProps) {
  return (
    <SessionProvider session={session}>
      <div className="flex flex-col h-full bg-zinc-950">
        <UserHeader />
        <div className="flex flex-1 h-[calc(100vh-3rem)] mt-12">
          <OntologyBar />
          <main className="flex-1 min-w-0 overflow-hidden">
            <ProjectView />
          </main>
          <div className="w-[400px] shrink-0">
            <Chatbot />
          </div>
        </div>
      </div>
    </SessionProvider>
  );
} 