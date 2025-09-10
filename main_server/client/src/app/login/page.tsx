import { getServerSession } from "next-auth/next"
import { authOptions } from "@/app/next-api/api/auth/[...nextauth]/route";
import LoginContainer from "@/app/login/container";




export default async function LoginPage() {
  const session = await getServerSession(authOptions);

  console.log(session);

  return (
    <LoginContainer session={session} />
  );
} 