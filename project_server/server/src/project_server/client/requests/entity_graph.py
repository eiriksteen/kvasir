from typing import List
from uuid import UUID

from project_server.client import ProjectClient
from synesis_schemas.main_server import (
    EdgesCreate,
    EntityDetailsResponse,
)


async def create_edges(client: ProjectClient, edges: EdgesCreate) -> str:
    response = await client.send_request(
        "post",
        "/entity-graph/edges",
        json=edges.model_dump(mode="json")
    )
    return response.body


async def remove_edges(client: ProjectClient, edges: EdgesCreate) -> str:
    response = await client.send_request(
        "delete",
        "/entity-graph/edges",
        json=edges.model_dump(mode="json")
    )
    return response.body


async def get_entity_details(client: ProjectClient, entity_ids: List[UUID]) -> EntityDetailsResponse:
    response = await client.send_request(
        "get",
        "/entity-graph/entity-details",
        params={"entity_ids": [str(entity_id) for entity_id in entity_ids]}
    )
    return EntityDetailsResponse(**response.body)
