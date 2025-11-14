'use client';

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import ProjectMenu from "@/app/projects/_components/ProjectMenu";
import UserHeader from "@/components/headers/UserHeader";
// import PublicHeader from "@/components/headers/PublicHeader";

interface SelectProjectContainerProps {
  session: Session;
}

function SelectProjectContent() {
  return (
    <div className="min-h-screen bg-white flex flex-col">
      <UserHeader />
      <div className="flex-1 flex items-center justify-center">
        <ProjectMenu/>
      </div>
    </div>
  );
}

export default function SelectProjectContainer({ session }: SelectProjectContainerProps) {
  return (
    <SessionProvider session={session} basePath="/next-api/api/auth">
      <SelectProjectContent />
    </SessionProvider>
  );
} 