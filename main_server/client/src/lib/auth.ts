import CredentialsProvider from "next-auth/providers/credentials"
import GoogleProvider from "next-auth/providers/google"
import { AuthOptions } from "next-auth"
import { User as UserType } from "@/types/next-auth"
import { snakeToCamelKeys, camelToSnakeKeys } from "@/lib/utils";
import { UserCreate, User } from "@/types/auth";

export const authOptions: AuthOptions = {

  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
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
    async jwt({ token, user, account, profile }) {

      // Handle Google OAuth sign-in
      if (account?.provider === "google" && profile?.email) {
        try {
          const response = await fetch(process.env.NEXT_PUBLIC_API_URL_INTERNAL + "/auth/google-login", {
            method: "POST",
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              email: profile.email,
              name: profile.name,
              google_id: profile.sub,
            }),
            credentials: "include",
          });

          if (!response.ok) {
            throw new Error("Failed to authenticate with Google");
          }

          const userData = snakeToCamelKeys(await response.json());
          token.APIToken = {
            accessToken: userData.accessToken,
            tokenExpiresAt: userData.tokenExpiresAt,
          };
          
          // Check if user needs to complete their profile
          if (userData.affiliation === "Unknown" || userData.role === "Unknown") {
            token.needsProfileCompletion = true;
          } else {
            token.needsProfileCompletion = false;
          }
          
          return token;
        } catch (error) {
          console.error("Error authenticating with Google:", error);
          return {
            ...token,
            error: "GoogleAuthError",
          };
        }
      }

      // Handle credentials sign-in
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
      session.needsProfileCompletion = token.needsProfileCompletion;
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

