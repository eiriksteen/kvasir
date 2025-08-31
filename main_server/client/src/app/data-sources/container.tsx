'use client';

import { SessionProvider } from "next-auth/react";
import { Session } from 'next-auth';
import UserHeader from "@/components/headers/UserHeader";
import { useDataSources } from "@/hooks/useDataSources";
import AddDataSourceMenu from "@/app/data-sources/_components/AddDataSourceMenu";
import DataSourceList from "@/app/data-sources/_components/DataSourceList";

interface SourcesContainerProps {
  session: Session;
}

function SourcesPageContent() {
  const { dataSources, error, isLoading } = useDataSources();

  return (
    <div className="flex h-full w-full bg-zinc-950 mt-12">
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-900/50">
          <div className="flex flex-col">
            <h1 className="text-base font-mono uppercase tracking-wider text-gray-400 mb-0.5">
              Data Sources
            </h1>
          </div>

        </div>

        Content
        <div className="flex-grow p-6 overflow-y-auto">
          <div className="grid grid-cols-2 gap-4">
            <DataSourceList dataSources={dataSources || []} isLoading={isLoading} error={error || null} />
            <AddDataSourceMenu />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SourcesContainer({ session }: SourcesContainerProps) {

  return (
    <SessionProvider session={session}>
      <div>
        <UserHeader projectId={undefined} />
        <div className="flex h-[calc(100vh-3rem)]">
          <SourcesPageContent />
        </div>
      </div>
    </SessionProvider>
  );
} 