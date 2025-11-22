import { getServerSession } from "next-auth/next"
import { authOptions } from "@/lib/auth";
import LoginContainer from "@/app/login/container";
import { redirect } from "next/navigation";




export default async function LoginPage() {
  const session = await getServerSession(authOptions);

  if (session) {
    redirect("/projects");
  }

  return (
    <LoginContainer session={session} />
  );
} 