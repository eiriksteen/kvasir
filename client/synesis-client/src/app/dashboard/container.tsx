'use client';

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import OntologyBar from "@/components/ontologyBar";
import Chatbot from "@/components/chatbot";
import UserHeader from "@/components/userHeader";

interface DashboardProps {
  session: Session;
}

export default function DashboardContainer({ session }: DashboardProps) {


  return (
    <SessionProvider session={session}>
      <div className="flex flex-col h-full bg-zinc-950">
        <UserHeader />
        <OntologyBar />
        <Chatbot />
      </div>
    </SessionProvider>
  );
} 