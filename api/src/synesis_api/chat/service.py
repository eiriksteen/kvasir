import uuid
from datetime import datetime
from sqlalchemy import select
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from .schema import ChatMessage, PydanticMessage, Conversation
from .models import chat_messages, pydantic_messages, conversations
from ..database.service import fetch_all, execute


async def create_conversation(user_id: uuid.UUID) -> Conversation:
    conversation = Conversation(
        id=uuid.uuid4(),
        user_id=user_id
    )
    await execute(conversations.insert().values(conversation.model_dump()), commit_after=True)
    return conversation


async def get_conversations(user_id: uuid.UUID) -> list[Conversation]:
    user_conversations = await fetch_all(
        select(conversations).where(
            conversations.c.user_id == user_id)
    )
    return [Conversation(**conversation) for conversation in user_conversations]


async def get_messages(conversation_id: uuid.UUID) -> list[ChatMessage]:
    messages = await fetch_all(
        select(chat_messages).where(
            chat_messages.c.conversation_id == conversation_id)
    )
    return [ChatMessage(**message) for message in messages]


async def get_messages_pydantic(conversation_id: uuid.UUID) -> list[ChatMessage]:
    c = await fetch_all(
        select(pydantic_messages).where(
            pydantic_messages.c.conversation_id == conversation_id)
    )
    messages: list[ModelMessage] = []
    for message in c:
        messages.extend(
            ModelMessagesTypeAdapter.validate_json(message["message_list"]))

    return messages


async def insert_message(conversation_id: uuid.UUID, role: str, content: str) -> ChatMessage:
    message = ChatMessage(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        role=role,
        content=content,
        created_at=datetime.now()
    )
    await execute(chat_messages.insert().values(message.model_dump()), commit_after=True)
    return message


async def insert_message_pydantic(conversation_id: uuid.UUID, messages: bytes) -> PydanticMessage:
    pydantic_message = PydanticMessage(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        message_list=messages
    )
    await execute(pydantic_messages.insert().values(pydantic_message.model_dump()), commit_after=True)
    return pydantic_message
