export type LocalDirectoryFile = {
  id: string;
  fileName: string;
  filePath: string;
  fileType: string;
  description: string;
};

export type LocalDirectoryDataSource = {
  id: string;
  directoryName: string;
  savePath: string;
  description: string;
  files: LocalDirectoryFile[];
};

export type IntegrationJobResult = {
  jobId: string;
  datasetId: string;
  codeExplanation: string;
};