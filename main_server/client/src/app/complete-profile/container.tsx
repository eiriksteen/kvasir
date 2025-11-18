'use client';

import CompleteProfileForm from "@/app/complete-profile/_components/CompleteProfileForm";
import { Session } from "next-auth";
import { SessionProvider } from "next-auth/react";

function CompleteProfileContent() {
    return <CompleteProfileForm />;
}

export default function CompleteProfileContainer({ session }: { session: Session | null }) {
    return (
        <SessionProvider session={session} basePath="/next-api/api/auth">
            <CompleteProfileContent />
        </SessionProvider>
    );
}

