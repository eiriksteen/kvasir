import { getServerSession } from "next-auth/next"
import { authOptions } from "@/lib/auth";
import { redirect } from "next/navigation";
import SelectProjectContainer from "@/app/projects/container";

export default async function SelectProjectPage() {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect('/login');
  }

  // Redirect to complete profile if needed
  if (session.needsProfileCompletion) {
    redirect('/complete-profile');
  }

  return (
    <SelectProjectContainer session={session} />
  );
} 