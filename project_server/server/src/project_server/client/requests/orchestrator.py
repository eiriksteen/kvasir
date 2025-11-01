import uuid
from typing import List

from project_server.client import ProjectClient
from synesis_schemas.main_server import (
    ConversationCreate,
    ConversationInDB,
    ChatMessage,
    ChatPydanticMessageInDB,
    ContextCreate,
    ContextInDB,
    ImplementationApprovalResponse,
)
from synesis_schemas.project_server import ImplementationSummary


async def post_conversation(client: ProjectClient, conversation_data: ConversationCreate) -> ConversationInDB:
    response = await client.send_request("post", "/orchestrator/conversation", json=conversation_data.model_dump(mode="json"))
    return ConversationInDB(**response.body)


async def get_messages(client: ProjectClient, conversation_id: uuid.UUID) -> List[ChatMessage]:
    response = await client.send_request("get", f"/orchestrator/messages/{conversation_id}")
    return [ChatMessage(**msg) for msg in response.body]


async def get_conversations(client: ProjectClient) -> List[ConversationInDB]:
    response = await client.send_request("get", "/orchestrator/conversations")
    return [ConversationInDB(**conv) for conv in response.body]


async def create_chat_message_pydantic_request(client: ProjectClient, conversation_id: uuid.UUID, messages: List[bytes]) -> List[ChatPydanticMessageInDB]:
    response = await client.send_request("post", f"/orchestrator/chat-message-pydantic/{conversation_id}", json=messages)
    return [ChatPydanticMessageInDB(**msg) for msg in response.body]


async def create_context_request(client: ProjectClient, context: ContextCreate) -> ContextInDB:
    response = await client.send_request("post", "/orchestrator/context", json=context.model_dump(mode="json"))
    return ContextInDB(**response.body)


async def post_swe_result_approval_request(client: ProjectClient, implementation_summary: ImplementationSummary) -> ImplementationApprovalResponse:
    response = await client.send_request("post", "/orchestrator/swe-result-approval-request", json=implementation_summary.model_dump(mode="json"))
    return ImplementationApprovalResponse(**response.body)
