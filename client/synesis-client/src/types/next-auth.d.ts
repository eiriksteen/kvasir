import NextAuth, { DefaultSession } from "next-auth"
import { JWT, DefaultJWT } from "next-auth/jwt"


export interface User {
  id: string;
  email: string;
  name: string;
  accessToken: string;
  tokenExpiresAt: string;
}

declare module "next-auth/jwt" {
  interface JWT extends DefaultJWT {
    APIToken: {
      accessToken: string;
      tokenExpiresAt: string;
    },
    error: string | undefined;
  } 
}

declare module "next-auth" {
  interface Session {
    user: User;
    APIToken: {
      accessToken: string;
      tokenExpiresAt: string;
    },
    error: string | undefined;
  }
}

