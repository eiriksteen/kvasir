import uuid
from datetime import datetime
from sqlalchemy import select
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from .schema import ChatMessage, PydanticMessage, Conversation, Context, Datasets, ContextInDB, DatasetContextInDB, AutomationContextInDB
from .models import chat_messages, pydantic_messages, conversations, context, dataset_context, automation_context
from ...database.service import fetch_all, execute, fetch_one
from ..ontology.service import get_user_datasets_by_ids


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
        message_list=messages,
        created_at=datetime.now()
    )
    await execute(pydantic_messages.insert().values(pydantic_message.model_dump()), commit_after=True)
    return pydantic_message


async def aggregate_context_from_db(context_record: ContextInDB) -> Context:
    dataset_ids = await fetch_all(
        select(dataset_context).where(
            dataset_context.c.context_id == context_record.id
        )
    )

    automation_ids = await fetch_all(
        select(automation_context).where(
            automation_context.c.context_id == context_record.id
        )
    )

    return Context(
        id=context_record.id,
        conversation_id=context_record.conversation_id,
        created_at=context_record.created_at,
        dataset_ids=tuple([record["dataset_id"] for record in dataset_ids]),
        automation_ids=tuple(
            [record["automation_id"] for record in automation_ids])
    )


async def insert_context(
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        dataset_ids: list[uuid.UUID],
        automation_ids: list[uuid.UUID]
) -> Context:

    context_record = ContextInDB(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        created_at=datetime.now()
    )

    dataset_context_records = [
        DatasetContextInDB(
            context_id=context_record.id,
            dataset_id=dataset_id
        )
        for dataset_id in dataset_ids
    ]

    automation_context_records = [
        AutomationContextInDB(
            context_id=context_record.id,
            automation_id=automation_id
        )
        for automation_id in automation_ids
    ]

    if len(dataset_context_records) == 0 and len(automation_context_records) == 0:
        return None
    else:
        await execute(context.insert().values(context_record.model_dump()), commit_after=True)
        if len(dataset_context_records) > 0:
            await execute(dataset_context.insert().values([record.model_dump() for record in dataset_context_records]), commit_after=True)
        if len(automation_context_records) > 0:
            await execute(automation_context.insert().values([record.model_dump() for record in automation_context_records]), commit_after=True)

    return await aggregate_context_from_db(context_record)


async def get_context_by_time_stamp(conversation_id: uuid.UUID, user_id: uuid.UUID, time_stamp: datetime) -> Context:

    context_record = await fetch_all(
        select(context).where(
            context.c.conversation_id == conversation_id,
            context.c.created_at <= time_stamp
        ).order_by(context.c.created_at.desc())
    )

    if len(context_record) == 0:
        return None
    else:
        context_record = ContextInDB(**context_record[0])
        return await aggregate_context_from_db(context_record)
