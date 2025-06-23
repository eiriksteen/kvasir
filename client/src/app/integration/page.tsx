import { getServerSession } from "next-auth/next"
import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import { redirect } from "next/navigation";
import IntegrationContainer from "@/app/integration/container";

export default async function IntegrationPage() {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect('/login');
  }

  return (
    <IntegrationContainer session={session} />
  );
} 