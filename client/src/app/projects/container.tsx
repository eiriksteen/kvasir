'use client';

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import ProjectMenu from "@/components/project/ProjectMenu";
import UserHeader from "@/components/headers/UserHeader";

interface SelectProjectContainerProps {
  session: Session;
}

function SelectProjectContent() {
  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col">
      <UserHeader projectId={undefined} />
      <div className="flex-1 flex items-center justify-center">
        <ProjectMenu/>
      </div>
    </div>
  );
}

export default function SelectProjectContainer({ session }: SelectProjectContainerProps) {
  return (
    <SessionProvider session={session}>
      <SelectProjectContent />
    </SessionProvider>
  );
} 