import CredentialsProvider from "next-auth/providers/credentials"
import { AuthOptions } from "next-auth"
import { User as UserType } from "@/types/next-auth"
import { snakeToCamelKeys, camelToSnakeKeys } from "@/lib/utils";
import { UserCreate, User } from "@/types/auth";

export const authOptions: AuthOptions = {

  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {return null;}
        
        try {
          const formData = new FormData();
          formData.append("username", credentials.email);
          formData.append("password", credentials.password);

          const response = await fetch(process.env.NEXT_PUBLIC_API_URL_INTERNAL + "/auth/login", {
            method: "POST",
            body: formData,
            credentials: "include", 
          });


          if (!response.ok) {
            const error = await response.text();
            throw new Error(error || "Failed to authenticate");
          }

          const user = snakeToCamelKeys(await response.json());
          return user;
        } catch (error) {
          throw error; 
        }
      },
    }),
  ],
  session: {strategy: "jwt"},
  secret: process.env.NEXTAUTH_SECRET,
  callbacks: {
    async jwt({ token, user }) {

      if (user as UserType) {
        token.APIToken = {
          accessToken: (user as UserType).accessToken,
          tokenExpiresAt: (user as UserType).tokenExpiresAt,
        };
        return token;
      }
      
      const tokenExpiresAt = new Date(token.APIToken?.tokenExpiresAt);
      const now = new Date();
      
      if (tokenExpiresAt && tokenExpiresAt < now) {

        try {
          const response = await fetch(process.env.NEXT_PUBLIC_API_URL_INTERNAL + "/auth/refresh", {
            method: "POST",
            credentials: "include", // Important for cookies
          });

        const refreshedUser = snakeToCamelKeys(await response.json());

        if (!response.ok) {
          throw refreshedUser
        }

        token.APIToken = {
          accessToken: refreshedUser.accessToken,
            tokenExpiresAt: refreshedUser.tokenExpiresAt,
          };
        } catch (error) {
          console.error("Error refreshing access token:", error);
          return {
            ...token,
            error: "RefreshAccessTokenError",
          }
        }
      }

      return token;
    },
    async session({ session, token }) {

      if (!token) {
        throw new Error("No token found");
      }
      session.APIToken = token.APIToken;
      session.error = token.error;
      return session;
    },
  },
  events: {
    async signOut() {
      try {
        await fetch(process.env.NEXT_PUBLIC_API_URL_INTERNAL + "/auth/signout", {
          method: "POST",
          credentials: "include",
        });
      } catch (error) {
        console.error("Error signing out from backend:", error);
      }
    },
  },
}

// Registration function
const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function registerUser(userData: UserCreate): Promise<User> {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(userData))
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to register' }));
    throw new Error(errorData.detail || `Failed to register: ${response.status}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

