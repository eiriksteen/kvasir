from typing import List
from pydantic import BaseModel
from bs4 import BeautifulSoup
import httpx


class PypiSearchResult(BaseModel):
    name: str
    version: str
    description: str


async def search_pypi_package(package_name: str) -> PypiSearchResult:
    url = f"https://pypi.org/pypi/{package_name}/json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        response_json = response.json()
        return PypiSearchResult(
            name=response_json["info"]["name"],
            version=response_json["info"]["version"],
            description=response_json["info"]["description"]
        )


def verify_package_and_version_in_search_results(search_results: List[PypiSearchResult], package_name: str, version: str) -> bool:
    for result in search_results:
        if result.name == package_name and result.version == version:
            return True
    return False
