import { UUID } from "crypto";


export interface Project {
  id: UUID;
  name: string;
  userId: UUID;
  viewPortX: number;
  viewPortY: number;
  viewPortZoom: number;
  description?: string | null;
  createdAt: string;
  updatedAt: string;
}


export interface ProjectCreate {
  name: string;
  mountGroupId?: UUID | null;
  description?: string | null;
}

