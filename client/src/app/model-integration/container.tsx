"use client";

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import ModelIntegrationManager from "@/components/model-integration/ModelIntegrationManager";

interface ModelIntegrationProps {
  session: Session;
}

export default function ModelIntegrationContainer({ session }: ModelIntegrationProps) {
  return (
    <SessionProvider session={session}>
      <div className="flex flex-col h-full bg-zinc-950">
        <main className="flex-1 h-[calc(100vh-4rem)]">
          <ModelIntegrationManager />
        </main>
      </div>
    </SessionProvider>
  );
} 