import { UUID } from "crypto";

// Role options
export const USER_ROLES = [
  "student",
  "non-technical",
  "researcher",
  "data-scientist",
  "data-engineer",
  "ml-engineer",
  "ml-ops",
  "other"
] as const;

export type UserRole = typeof USER_ROLES[number];

// Base schemas

export interface UserBase {
  email: string;
  name: string;
  affiliation: string;
  role: string;
  disabled: boolean;
  googleId?: string | null;
}

export interface UserCreate extends UserBase {
  password: string;
}

export interface User extends UserBase {
  id: UUID;
  createdAt: string;
  updatedAt: string;
}

export interface UserInDB extends User {
  hashedPassword: string;
}

export interface UserWithToken extends User {
  accessToken: string;
  tokenType: string;
  tokenExpiresAt: string;
}

export interface TokenData {
  userId: string;
}

export interface UserAPIKey {
  id: UUID;
  userId: UUID;
  key: string;
  expiresAt: string;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface JWKSEntry {
  kid: string;
  kty: string;
  alg: string;
  use: string;
  crv: string;
  x: Uint8Array; // bytes in Python
  y: Uint8Array; // bytes in Python
}

export interface JWKSData {
  keys: JWKSEntry[];
}

