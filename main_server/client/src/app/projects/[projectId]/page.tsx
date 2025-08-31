import { getServerSession } from "next-auth/next"
import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import { redirect } from "next/navigation";
import ProjectContainer from "@/app/projects/[projectId]/container";
import { UUID } from "crypto";


interface ProjectPageProps {
  params: Promise<{
    projectId: UUID;
  }>;
}

export default async function ProjectPage({ params }: ProjectPageProps) {
  const session = await getServerSession(authOptions);
  const { projectId } = await params;

  if (!session) {
    redirect("/login");
  }

  return (
    <ProjectContainer projectId={projectId} session={session} />
  );
}
