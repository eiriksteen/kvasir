export interface CodebaseFile {
  path: string;
  content: string;
}

export interface CodebasePath {
  path: string;
  isFile: boolean;
  subPaths: CodebasePath[];
}

