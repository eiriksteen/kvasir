'use client';

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import UserHeader from "@/components/headers/UserHeader";
import DatasetsPageContent from "./page-content";

interface DatasetsContainerProps {
  session: Session;
}

export default function DatasetsContainer({ session }: DatasetsContainerProps) {
  return (
    <SessionProvider session={session}>
      <div>
        <UserHeader projectId={undefined} />
        <div className="flex h-[calc(100vh-3rem)]">
            <DatasetsPageContent />
        </div>
      </div>
    </SessionProvider>
  );
} 