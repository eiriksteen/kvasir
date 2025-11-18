'use client';

import RegisterForm from "@/app/register/_components/RegisterForm";
import { Session } from "next-auth";
import { SessionProvider } from "next-auth/react";

function RegisterContent() {
    return <RegisterForm />;
}

export default function RegisterContainer({ session }: { session: Session | null }) {
    return (
        <SessionProvider session={session} basePath="/next-api/api/auth">
            <RegisterContent />
        </SessionProvider>
    );
}

