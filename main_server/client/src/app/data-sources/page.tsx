import { getServerSession } from "next-auth/next"
import { authOptions } from "@/app/next-api/api/auth/[...nextauth]/route";
import { redirect } from "next/navigation";
import SourcesContainer from "@/app/data-sources/container";

export default async function SourcesPage() {
  const session = await getServerSession(authOptions);

  if (!session || session?.error) {
    redirect('/login');
  }

  return (
    <SourcesContainer session={session} />
  );
} 