import { getServerSession } from "next-auth/next"
import { authOptions } from "@/app/next-api/auth/[...nextauth]/route";
import { redirect } from "next/navigation";
import SelectProjectContainer from "@/app/projects/container";

export default async function SelectProjectPage() {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect('/login');
  }

  return (
    <SelectProjectContainer session={session} />
  );
} 