import aiohttp
from typing import Literal
from aiohttp import ClientResponse

from project_server.secrets import MAIN_SERVER_URL, USERNAME, PASSWORD


class ProjectClient:

    def __init__(self):
        self.bearer_token = None
        self.refresh_tries = 0
        self.max_refresh_tries = 3

    async def send_request(self, method: Literal["get", "post", "put", "delete"], path: str, kwargs: dict) -> ClientResponse:
        if self.bearer_token is None:
            await self.login()

        headers = {'Authorization': f'Bearer {self.bearer_token}'}

        async with aiohttp.ClientSession() as session:
            async with session.request(method, f"{MAIN_SERVER_URL}{path}", headers=headers, **kwargs) as response:

                if response.status == 401:
                    if self.refresh_tries >= self.max_refresh_tries:
                        raise RuntimeError("Max tries reached")

                    else:
                        await self.refresh_token()
                        response = await self.send_request(method, path, kwargs)
                        self.refresh_tries += 1

                return response

    async def login(self) -> None:
        response = await self.send_request("post", "/auth/login", {
            "email": USERNAME,
            "password": PASSWORD
        })

        self.bearer_token = response.headers["Authorization"]

    async def refresh_token(self) -> None:
        response = await self.send_request("post", "/auth/refresh", {})
        self.bearer_token = response.headers["Authorization"]

    async def logout(self) -> None:
        await self.send_request("post", "/auth/logout", {})
        self.bearer_token = None


project_client = ProjectClient()
