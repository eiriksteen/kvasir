from typing import List
from uuid import UUID

from project_server.client import ProjectClient
from synesis_schemas.main_server import FrontendNode, FrontendNodeCreate


async def post_create_node(client: ProjectClient, node: FrontendNodeCreate) -> FrontendNode:
    response = await client.send_request("post", "/node/create-node", json=node.model_dump(mode="json"))
    return FrontendNode(**response.body)


async def get_project_nodes(client: ProjectClient, project_id: UUID) -> List[FrontendNode]:
    response = await client.send_request("get", f"/node/project/{project_id}")
    return [FrontendNode(**node) for node in response.body]


async def put_update_node(client: ProjectClient, node: FrontendNode) -> FrontendNode:
    response = await client.send_request("put", f"/node/update-node/{node.id}", json=node.model_dump(mode="json"))
    return FrontendNode(**response.body)


async def delete_node(client: ProjectClient, node_id: UUID) -> UUID:
    response = await client.send_request("delete", f"/node/delete/{node_id}")
    return UUID(response.body)
