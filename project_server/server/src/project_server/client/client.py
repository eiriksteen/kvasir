import aiohttp
from typing import Literal, Optional
from attr import dataclass

from project_server.app_secrets import MAIN_SERVER_URL


@dataclass
class ProjectClientResponse:
    status: int
    headers: dict
    body: dict
    content_type: str


class ProjectClient:

    def __init__(self, bearer_token: Optional[str] = None):
        self.bearer_token = bearer_token
        self.refresh_tries = 0
        self.max_refresh_tries = 3

    def set_bearer_token(self, bearer_token: str):
        self.bearer_token = bearer_token

    async def send_request(
        self,
        method: Literal["get", "post", "put", "delete", "patch"],
        path: str,
        data: Optional[dict] = None,
        json: Optional[dict] = None,
        headers: dict = {}
    ) -> ProjectClientResponse:

        if self.bearer_token:
            headers["Authorization"] = f'Bearer {self.bearer_token}'

        async with aiohttp.ClientSession() as session:
            async with session.request(method, f"{MAIN_SERVER_URL}{path}", headers=headers, data=data, json=json) as response:

                if response.status == 401:
                    if self.refresh_tries >= self.max_refresh_tries:
                        raise RuntimeError("Max tries reached")
                    else:
                        await self.refresh_token()
                        response = await self.send_request(method, path, data, json, headers)
                        self.refresh_tries += 1

                return ProjectClientResponse(
                    status=response.status,
                    headers=dict(response.headers),
                    # We assume the response is json, maybe should be more robust
                    body=await response.json(),
                    content_type=response.headers.get('content-type', '')
                )

    async def refresh_token(self) -> None:
        if self.bearer_token is None:
            raise RuntimeError("Bearer token is not set")

        response = await self.send_request("post", "/auth/refresh")
        self.bearer_token = response.headers["Authorization"]
