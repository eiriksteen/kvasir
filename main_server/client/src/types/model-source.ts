import { UUID } from "crypto";

export type SupportedModelSource = "github" | "pypi" | "gitlab" | "huggingface" | "local";


export interface ModelSourceBase {
  id: UUID;
  user_id: string;
  type: SupportedModelSource;
  name: string;
  createdAt: string;
  updatedAt: string;
}

export interface PypiModelSource extends ModelSourceBase {
  type: "pypi";
  packageName: string;
  packageVersion: string;
}

export type ModelSource = PypiModelSource // | GithubModelSource | GitlabModelSource | HuggingfaceModelSource | LocalModelSource;