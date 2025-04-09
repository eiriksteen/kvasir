import CredentialsProvider from "next-auth/providers/credentials"
import NextAuth, { AuthOptions } from "next-auth"
import { User as UserType } from "@/types/next-auth"


export const authOptions: AuthOptions = {

  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;
        
        try {
          const formData = new FormData();
          formData.append("username", credentials.email);
          formData.append("password", credentials.password);

          const response = await fetch(process.env.API_URL + "/auth/login", {
            method: "POST",
            body: formData,
            credentials: "include", 
          });

          if (!response.ok) {
            const error = await response.text();
            throw new Error(error || "Failed to authenticate");
          }

          const user = await response.json();
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

          const response = await fetch(process.env.API_URL + "/auth/refresh", {
            method: "POST",
            credentials: "include", // Important for cookies
          });

        const refreshedUser = await response.json();

        if (!response.ok) {
          throw refreshedUser
        }

        token.APIToken = {
          accessToken: refreshedUser.accessToken,
            tokenExpiresAt: refreshedUser.tokenExpiresAt,
          };
        } catch (error) {

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
}

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };