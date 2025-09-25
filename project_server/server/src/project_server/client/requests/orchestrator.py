import uuid
from typing import List

from project_server.client import ProjectClient
from synesis_schemas.main_server import (
    ConversationCreate,
    ConversationInDB,
    ChatMessage
)


async def post_conversation(client: ProjectClient, conversation_data: ConversationCreate) -> ConversationInDB:
    response = await client.send_request("post", "/orchestrator/conversation", json=conversation_data.model_dump(mode="json"))
    return ConversationInDB(**response.body)


async def get_messages(client: ProjectClient, conversation_id: uuid.UUID) -> List[ChatMessage]:
    response = await client.send_request("get", f"/orchestrator/messages/{conversation_id}")
    return [ChatMessage(**msg) for msg in response.body]


async def get_conversations(client: ProjectClient) -> List[ConversationInDB]:
    response = await client.send_request("get", "/orchestrator/conversations")
    return [ConversationInDB(**conv) for conv in response.body]
