import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { Session } from "next-auth";


export async function getSession() : Promise<Session | null> {

    const session = await getServerSession(authOptions);

    if (session?.error === "RefreshAccessTokenError") {
        console.error("Error refreshing access token:", session.error);
        return null;
    }
    else if (session?.error) {
        console.error("Error getting session:", session.error);
        throw new Error(session.error);
    }

    return session;
}