import re


def parse_github_url(github_url: str) -> dict[str, str]:
    """
    Parse a GitHub URL and return the owner and repository name.
    """
    match = re.search(
        r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$', github_url)
    if not match:
        return "Invalid GitHub URL format"

    owner, repo = match.groups()

    return {
        "owner": owner,
        "repo": repo
    }
