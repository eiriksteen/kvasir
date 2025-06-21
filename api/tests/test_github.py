from __future__ import annotations as _annotations

import asyncio
import os
from dataclasses import dataclass
import re
import httpx
from pydantic_ai import Agent, RunContext

from synesis_api.utils import get_model
from synesis_api.secrets import GITHUB_TOKEN

model = get_model()


@dataclass
class GitHubDeps:
    client: httpx.AsyncClient
    github_token: str | None = None


system_prompt = """
You are a coding expert with access to GitHub to help the user manage their repository and get information from it.

Your only job is to assist with this and you don't answer other questions besides describing what you are able to do.

Don't ask the user before taking an action, just do it. Always make sure you look at the repository with the provided tools before answering the user's question unless you have already.

When answering a question about the repo, always start your answer with the full repo URL in brackets and then give your answer on a newline. Like:

[Using https://github.com/[repo URL from the user]]

Your answer here...
"""


github_agent = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=GitHubDeps,
    retries=2
)


@github_agent.tool
async def get_repo_info(ctx: RunContext[GitHubDeps], github_url: str) -> str:
    """Get repository information including size and description using GitHub API.

    Args:
        ctx: The context.
        github_url: The GitHub repository URL.

    Returns:
        str: Repository information as a formatted string.
    """
    match = re.search(
        r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$', github_url)
    if not match:
        return "Invalid GitHub URL format"

    owner, repo = match.groups()
    headers = {
        'Authorization': f'token {ctx.deps.github_token}'} if ctx.deps.github_token else {}

    response = await ctx.deps.client.get(
        f'https://api.github.com/repos/{owner}/{repo}',
        headers=headers
    )

    if response.status_code != 200:
        return f"Failed to get repository info: {response.text}"

    data = response.json()
    size_mb = data['size'] / 1024

    return (
        f"Repository: {data['full_name']}\n"
        f"Description: {data['description']}\n"
        f"Size: {size_mb:.1f}MB\n"
        f"Stars: {data['stargazers_count']}\n"
        f"Language: {data['language']}\n"
        f"Created: {data['created_at']}\n"
        f"Last Updated: {data['updated_at']}"
    )


@github_agent.tool
async def get_repo_structure(ctx: RunContext[GitHubDeps], github_url: str) -> str:
    """Get the directory structure of a GitHub repository.

    Args:
        ctx: The context.
        github_url: The GitHub repository URL.

    Returns:
        str: Directory structure as a formatted string.
    """
    match = re.search(
        r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$', github_url)
    if not match:
        return "Invalid GitHub URL format"

    owner, repo = match.groups()
    headers = {
        'Authorization': f'token {ctx.deps.github_token}'} if ctx.deps.github_token else {}

    response = await ctx.deps.client.get(
        f'https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1',
        headers=headers
    )

    if response.status_code != 200:
        # Try with master branch if main fails
        response = await ctx.deps.client.get(
            f'https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1',
            headers=headers
        )
        if response.status_code != 200:
            return f"Failed to get repository structure: {response.text}"

    data = response.json()
    tree = data['tree']

    # Build directory structure
    structure = []
    for item in tree:
        if not any(excluded in item['path'] for excluded in ['.git/', 'node_modules/', '__pycache__/']):
            structure.append(
                f"{'📁 ' if item['type'] == 'tree' else '📄 '}{item['path']}")

    return "\n".join(structure)


@github_agent.tool
async def get_file_content(ctx: RunContext[GitHubDeps], github_url: str, file_path: str) -> str:
    """Get the content of a specific file from the GitHub repository.

    Args:
        ctx: The context.
        github_url: The GitHub repository URL.
        file_path: Path to the file within the repository.

    Returns:
        str: File content as a string.
    """
    match = re.search(
        r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$', github_url)
    if not match:
        return "Invalid GitHub URL format"

    owner, repo = match.groups()
    headers = {
        'Authorization': f'token {ctx.deps.github_token}'} if ctx.deps.github_token else {}

    response = await ctx.deps.client.get(
        f'https://raw.githubusercontent.com/{owner}/{repo}/main/{file_path}',
        headers=headers
    )

    if response.status_code != 200:
        # Try with master branch if main fails
        response = await ctx.deps.client.get(
            f'https://raw.githubusercontent.com/{owner}/{repo}/master/{file_path}',
            headers=headers
        )
        if response.status_code != 200:
            return f"Failed to get file content: {response.text}"

    return response.text


async def main():

    github_url = "https://github.com/kwuking/TimeMixer"

    deps = GitHubDeps(
        client=httpx.AsyncClient(),
        github_token=GITHUB_TOKEN
    )

    async with github_agent.iter(
        f"Please analyze the repository and provide a summary of the project, the URL is {github_url}. Inspect a selected file in the repo and provide a summary of the file.",
        github_url=github_url,
        deps=deps
    ) as agent_run:
        async for node in agent_run:
            print(node)


if __name__ == "__main__":
    asyncio.run(main())
