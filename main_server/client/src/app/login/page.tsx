import { getServerSession } from "next-auth/next"
import { authOptions } from "@/app/next-api/api/auth/[...nextauth]/route";
import LoginContainer from "@/app/login/container";
import { redirect } from "next/navigation";




export default async function LoginPage() {
  const session = await getServerSession(authOptions);

  if (session && !session?.error) {
    redirect("/projects");
  }

  return (
    <LoginContainer session={session} />
  );
} 