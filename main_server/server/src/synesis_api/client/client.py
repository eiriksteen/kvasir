import aiohttp
from typing import Literal, Optional
from attr import dataclass

from synesis_api.app_secrets import PROJECT_SERVER_URL


@dataclass
class MainServerClientResponse:
    status: int
    headers: dict
    body: bytes
    content_type: str


class MainServerClient:

    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.refresh_tries = 0
        self.max_refresh_tries = 3

    async def send_request(
            self,
            method: Literal["get", "post", "put", "delete"],
            path: str,
            data: Optional[dict] = None,
            json: Optional[dict] = None,
            headers: dict = {}) -> MainServerClientResponse:

        headers["Authorization"] = f'Bearer {self.bearer_token}'

        async with aiohttp.ClientSession() as session:
            async with session.request(method, f"{PROJECT_SERVER_URL}{path}", headers=headers, data=data, json=json) as response:

                if response.status == 401:
                    if self.refresh_tries >= self.max_refresh_tries:
                        raise RuntimeError("Max tries reached")

                    else:
                        response = await self.send_request(method, path, data, json, headers)
                        self.refresh_tries += 1

                return MainServerClientResponse(
                    status=response.status,
                    headers=dict(response.headers),
                    # We assume the response is json, maybe should be more robust
                    body=await response.json(),
                    content_type=response.headers.get('content-type', '')
                )
