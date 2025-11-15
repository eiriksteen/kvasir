import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import RegisterContainer from "./container";

export default async function RegisterPage() {
  const session = await getServerSession(authOptions);
  return <RegisterContainer session={session} />;
}
