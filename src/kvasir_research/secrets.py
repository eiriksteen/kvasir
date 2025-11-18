from pathlib import Path

SUPPORTED_MODELS = [
    "o4-mini",
    "claude-3-5-sonnet-latest",
    "gemini-2.5-flash",
    "o3",
    "gemini-2.5-pro",
    "gpt-5",
    "grok-code-fast-1",
    "grok-4",
]

MODEL_TO_USE = "grok-code-fast-1"
OPENAI_API_KEY = "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"
ANTHROPIC_API_KEY = "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"
GOOGLE_API_KEY = "AIzaSyCKBc3cUZWtqrmipfestZqO6bkw3MjpRZU"
XAI_API_KEY = "xai-KzbcnESSJAR33iPBF0I4vFvhGwAWPu1aPfPLBTeMPvvUZnXX9eKls9da40weJIWoIsvnMvO6BEZ2VV40"
AWS_ACCESS_KEY_ID = "AKIATHVQKXLHEUZCZIYH"


CODEBASE_HOST_DIR = Path(
    "/Users/eiriksteen/Personal/project/kvasir-research/exp")
CODEBASE_DIR = Path("/app/exp")

SANDBOX_PYPROJECT_HOST_PATH = Path(
    "/Users/eiriksteen/Personal/project/kvasir-research/src/kvasir_research/sandbox/pyproject.toml")
SANDBOX_PYPROJECT_PATH = Path(
    "/app/kvasir-research/src/kvasir_research/sandbox/pyproject.toml")


READABLE_EXTENSIONS = {
    ".py", ".txt", ".md", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".sh", ".bash", ".zsh", ".xml", ".html", ".css", ".js", ".ts", ".jsx", ".tsx",
    ".sql", ".log"
}


REDIS_URL = "redis://host.docker.internal:6379/1"

PROJECTS_DIR = Path("/app/projects_dir")
PROJECTS_HOST_DIR = Path(
    "/Users/eiriksteen/Personal/project/kvasir-research/projects_dir")


MODAL_APP_NAME = "kvasir-research"
MODAL_PROJECTS_DIR = Path("/projects")

SANDBOX_DOCKERFILE_PATH = Path(
    "/app/kvasir-research/src/kvasir_research/sandbox/Dockerfile")
SANDBOX_INTERNAL_SCRIPT_DIR = Path("/app/internal")
