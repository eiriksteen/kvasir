import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { Session } from "next-auth";


export async function getSession() : Promise<Session | null> {
    const session = await getServerSession(authOptions);
    
    // If session is null (refresh failed), return null to trigger redirect to login
    if (!session) {
        return null;
    }
    
    // Only ignore refresh token errors - raise other errors normally
    if (session.error === "RefreshAccessTokenError") {
        return null;
    }
    
    // Raise other errors
    if (session.error) {
        throw new Error(session.error);
    }

    return session;
}