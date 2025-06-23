'use client';

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import UserHeader from "@/components/UserHeader";
import IntegrationPageContent from "./page-content";

interface IntegrationContainerProps {
  session: Session;
}

export default function IntegrationContainer({ session }: IntegrationContainerProps) {
  return (
    <SessionProvider session={session}>
      <div>
        <UserHeader />
        <div className="flex h-[calc(100vh-3rem)]">
            <IntegrationPageContent />
        </div>
      </div>
    </SessionProvider>
  );
} 