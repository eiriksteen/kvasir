import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from synesis_api.modules.chat.schema import ChatMessage, PydanticMessage, Conversation, Context, Datasets, ContextInDB, DatasetContextInDB, AutomationContextInDB, AnalysisContextInDB
from synesis_api.modules.chat.models import chat_message, pydantic_message, conversations, context, dataset_context, automation_context, analysis_context
from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.ontology.service import get_user_datasets_by_ids


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
        select(chat_message).where(
            chat_message.c.conversation_id == conversation_id)
    )
    return [ChatMessage(**message) for message in messages]


async def get_messages_pydantic(conversation_id: uuid.UUID) -> list[ModelMessage]:
    c = await fetch_all(
        select(pydantic_message).where(
            pydantic_message.c.conversation_id == conversation_id)
    )
    messages: list[ModelMessage] = []
    for message in c:
        messages.extend(
            ModelMessagesTypeAdapter.validate_json(message["message_list"]))

    return messages


async def create_message(conversation_id: uuid.UUID, role: str, content: str) -> ChatMessage:
    message = ChatMessage(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        role=role,
        content=content,
        created_at=datetime.now(timezone.utc)
    )
    await execute(chat_message.insert().values(message.model_dump()), commit_after=True)
    return message


async def create_messages_pydantic(conversation_id: uuid.UUID, messages: bytes) -> PydanticMessage:
    message = PydanticMessage(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        message_list=messages,
        created_at=datetime.now(timezone.utc)
    )
    await execute(pydantic_message.insert().values(message.model_dump()), commit_after=True)
    return message


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

    analysis_ids = await fetch_all(
        select(analysis_context).where(
            analysis_context.c.context_id == context_record.id
        )
    )

    return Context(
        id=context_record.id,
        conversation_id=context_record.conversation_id,
        created_at=context_record.created_at,
        dataset_ids=tuple([record["dataset_id"] for record in dataset_ids]),
        automation_ids=tuple([record["automation_id"] for record in automation_ids]),
        analysis_ids=tuple([record["analysis_id"] for record in analysis_ids])
    )


async def create_context(
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        dataset_ids: list[uuid.UUID],
        automation_ids: list[uuid.UUID],
        analysis_ids: list[uuid.UUID]
) -> Context:
    context_record = ContextInDB(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        created_at=datetime.now(timezone.utc),
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

    analysis_context_records = [
        AnalysisContextInDB(
            context_id=context_record.id,
            analysis_id=analysis_id
        )
        for analysis_id in analysis_ids
    ]

    if len(dataset_context_records) == 0 and len(automation_context_records) == 0 and len(analysis_context_records) == 0:
        return None
    else:
        await execute(context.insert().values(context_record.model_dump()), commit_after=True)
        if len(dataset_context_records) > 0:
            await execute(dataset_context.insert().values([record.model_dump() for record in dataset_context_records]), commit_after=True)
        if len(automation_context_records) > 0:
            await execute(automation_context.insert().values([record.model_dump() for record in automation_context_records]), commit_after=True)
        if len(analysis_context_records) > 0:
            await execute(analysis_context.insert().values([record.model_dump() for record in analysis_context_records]), commit_after=True)

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
