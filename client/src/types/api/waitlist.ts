import { UUID } from "crypto";

// Database model
export interface WaitlistInDB {
  id: UUID;
  email: string;
  name: string;
  affiliation: string;
  role: string;
  createdAt: string;
}

// Create model
export interface WaitlistCreate {
  email: string;
  name: string;
  affiliation: string;
  role: string;
}

