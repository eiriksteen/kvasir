import { getServerSession } from "next-auth/next"
import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import { redirect } from "next/navigation";
import ModelIntegrationContainer from "@/app/model-integration/container";

export default async function ModelIntegrationPage() {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect('/login');
  }

  return (
    <ModelIntegrationContainer session={session} />
  );
}
