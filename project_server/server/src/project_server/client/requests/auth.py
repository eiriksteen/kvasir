from project_server.client import ProjectClient
from synesis_schemas.main_server import UserCreate, UserWithToken, User, JWKSData


async def post_login(client: ProjectClient, username: str, password: str) -> UserWithToken:
    response = await client.send_request("post", "/auth/login", json={
        "username": username,
        "password": password
    })
    return UserWithToken(**response.body)


async def post_refresh(client: ProjectClient) -> UserWithToken:
    response = await client.send_request("post", "/auth/refresh")
    return UserWithToken(**response.body)


async def post_register(client: ProjectClient, user_create: UserCreate) -> User:
    response = await client.send_request("post", "/auth/register", json=user_create.model_dump(mode="json"))
    return User(**response.body)


async def get_current_user(client: ProjectClient) -> User:
    response = await client.send_request("get", "/auth/current-user")
    return User(**response.body)


async def get_jwks(client: ProjectClient) -> JWKSData:
    response = await client.send_request("get", "/auth/.well-known/jwks.json")
    return JWKSData(**response.body)
