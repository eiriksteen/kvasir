'use client';

import Link from "next/link";
import { redirect } from 'next/navigation';

import LoginForm from "@/app/login/_components/LoginForm";
import { Session } from "next-auth";
import { SessionProvider } from "next-auth/react";


function LoginContent() {

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


export default function LoginContainer({ session }: { session: Session | null }) {

    console.log("SESSION")
    console.log(session);

    if (session) {
        redirect('/projects');
    }

    return (
        <SessionProvider session={session} basePath="/next-api/api/auth">
            <LoginContent />
        </SessionProvider>
    );
} 