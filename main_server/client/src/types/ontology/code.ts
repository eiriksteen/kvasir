export interface CodebaseFile {
  path: string;
  content: string;
}

export interface CodebaseFilePaginated {
  path: string;
  content: string;
  offset: number;
  limit: number;
  totalLines: number;
  hasMore: boolean;
}

export interface CodebasePath {
  path: string;
  isFile: boolean;
  subPaths: CodebasePath[];
}

