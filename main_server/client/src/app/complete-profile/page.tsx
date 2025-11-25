import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { redirect } from "next/navigation";
import CompleteProfileContainer from "./container";

export default async function CompleteProfilePage() {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect("/login");
  }

  if (!session.needsProfileCompletion) {
    redirect("/projects");
  }

  return <CompleteProfileContainer session={session} />;
}

