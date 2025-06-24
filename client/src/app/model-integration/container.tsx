"use client";

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import UserHeader from "@/components/headers/UserHeader";
import ModelIntegrationPageContent from "@/app/model-integration/page-content";

interface ModelIntegrationProps {
  session: Session;
}

export default function ModelIntegrationContainer({ session }: ModelIntegrationProps) {
  return (
    <SessionProvider session={session}>
      <div>
        <UserHeader projectId={undefined} />
        <div className="flex h-[calc(100vh-3rem)]">
          <ModelIntegrationPageContent />
        </div>
      </div>
    </SessionProvider>
  );
} 