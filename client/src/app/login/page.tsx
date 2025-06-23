import Link from "next/link";
import { redirect } from 'next/navigation';
import { getSession } from "@/lib/getSession";
import LoginForm from "./form";



export default async function Login() {
    const session = await getSession();

    if (session) {
        redirect('/select-project');
    }

    return (
        <div className="grid pt-32 items-center justify-items-center min-h-screen font-[family-name:var(--font-geist-sans)]">
            <LoginForm />
            <Link 
                href="/register"
                className="block text-center text-white hover:text-gray-300 mt-4 text-sm">
                Don&apos;t have an account? Register here
            </Link>
        </div>
    );
} 