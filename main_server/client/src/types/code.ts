
export interface ProjectPath {
  path: string;
  isFile: boolean;
  subPaths: ProjectPath[];
}

