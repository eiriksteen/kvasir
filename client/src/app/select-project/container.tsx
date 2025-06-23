'use client';

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import SelectProject from "@/components/SelectProject";
import { useRouter } from "next/navigation";
import UserHeader from "@/components/UserHeader";

interface SelectProjectContainerProps {
  session: Session;
}

function SelectProjectContent() {
  const router = useRouter();

  const handleProjectSelect = () => {
    router.push('/dashboard');
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col">
      <UserHeader />
      <div className="flex-1 flex items-center justify-center">
        <SelectProject onSelect={handleProjectSelect} />
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