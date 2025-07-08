'use client';

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import UserHeader from "@/components/headers/UserHeader";
import ModelsPageContent from "./page-content";

interface ModelsContainerProps {
  session: Session;
}

export default function ModelsContainer({ session }: ModelsContainerProps) {
  return (
    <SessionProvider session={session}>
      <div>
        <UserHeader projectId={undefined} />
        <div className="flex h-[calc(100vh-3rem)]">
            <ModelsPageContent />
        </div>
      </div>
    </SessionProvider>
  );
} 