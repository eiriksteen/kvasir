import uuid
from datetime import datetime, timezone
from typing import Literal, Optional
from sqlalchemy import select
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from synesis_api.modules.chat.schema import (
    ChatMessage,
    PydanticMessage,
    Conversation,
    Context,
    ContextInDB,
    DatasetContextInDB,
    AutomationContextInDB,
    AnalysisContextInDB,
    ConversationInDB,
    ConversationModeInDB)
from synesis_api.modules.chat.models import (
    chat_message,
    pydantic_message,
    conversations,
    context,
    dataset_context,
    automation_context, analysis_context, conversation_mode)
from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.data_objects.service import get_user_datasets_by_ids
from synesis_api.modules.analysis.service import get_user_analyses_by_ids


async def create_conversation(conversation_id: uuid.UUID, project_id: uuid.UUID, user_id: uuid.UUID, name: str) -> ConversationInDB:
    conversation = ConversationInDB(
        id=conversation_id,
        user_id=user_id,
        project_id=project_id,
        name=name,
    )
    await execute(conversations.insert().values(conversation.model_dump()), commit_after=True)
    return conversation


async def get_conversations(user_id: uuid.UUID) -> list[Conversation]:
    user_conversations = await fetch_all(
        select(conversations).where(
            conversations.c.user_id == user_id)
    )

    conversation_list = []
    for conversation_data in user_conversations:
        # Get messages for this conversation
        messages = await get_messages(conversation_data["id"])

        # Create Conversation object with messages
        conversation = Conversation(
            **conversation_data,
            messages=messages
        )
        conversation_list.append(conversation)

    return conversation_list


async def get_messages(conversation_id: uuid.UUID) -> list[ChatMessage]:
    messages = await fetch_all(
        select(chat_message).where(
            chat_message.c.conversation_id == conversation_id)
    )

    chat_messages = []
    for message_data in messages:
        # Get the context data if context_id exists
        context_obj = None
        if message_data["context_id"]:
            context_obj = await get_context_by_id(message_data["context_id"])

        # Create ChatMessage with full context
        chat_message_obj = ChatMessage(
            id=message_data["id"],
            conversation_id=message_data["conversation_id"],
            role=message_data["role"],
            content=message_data["content"],
            context=context_obj,
            created_at=message_data["created_at"]
        )
        chat_messages.append(chat_message_obj)

    return chat_messages


async def get_context_by_id(context_id: uuid.UUID) -> Context | None:
    """Fetch a complete Context object by its ID"""
    # Get the base context
    context_data = await fetch_one(
        select(context).where(context.c.id == context_id)
    )

    if not context_data:
        return None

    # Get related dataset IDs
    dataset_contexts = await fetch_all(
        select(dataset_context).where(
            dataset_context.c.context_id == context_id)
    )
    dataset_ids = [dc["dataset_id"] for dc in dataset_contexts]

    # Get related automation IDs
    automation_contexts = await fetch_all(
        select(automation_context).where(
            automation_context.c.context_id == context_id)
    )
    automation_ids = [ac["automation_id"] for ac in automation_contexts]

    # Get related analysis IDs
    analysis_contexts = await fetch_all(
        select(analysis_context).where(
            analysis_context.c.context_id == context_id)
    )
    analysis_ids = [ac["analysis_id"] for ac in analysis_contexts]

    # Construct the full Context object
    return Context(
        id=context_data["id"],
        project_id=context_data["project_id"],
        dataset_ids=dataset_ids,
        automation_ids=automation_ids,
        analysis_ids=analysis_ids
    )


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


async def create_message(
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        type: Literal["tool_call", "result", "error", "chat"],
        job_id: Optional[uuid.UUID] = None,
        context_id: Optional[uuid.UUID] = None) -> ChatMessage:
    # Create the message in database using ChatMessageInDB structure
    message_id = uuid.uuid4()
    message_data = {
        "id": message_id,
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "type": type,
        "job_id": job_id,
        "context_id": context_id,
        "created_at": datetime.now(timezone.utc)
    }

    await execute(chat_message.insert().values(message_data), commit_after=True)

    # Get the full context if context_id exists
    context_obj = None
    if context_id:
        context_obj = await get_context_by_id(context_id)

    # Return the full ChatMessage with context
    return ChatMessage(
        id=message_id,
        conversation_id=conversation_id,
        role=role,
        content=content,
        context=context_obj,
        created_at=message_data["created_at"]
    )


async def create_messages_pydantic(conversation_id: uuid.UUID, messages: bytes) -> PydanticMessage:
    message = PydanticMessage(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        message_list=messages,
        created_at=datetime.now(timezone.utc)
    )
    await execute(pydantic_message.insert().values(message.model_dump()), commit_after=True)
    return message


async def create_context(
        context_data: Context
) -> Context:
    context_id = uuid.uuid4()

    context_record = ContextInDB(
        id=context_id,
        project_id=context_data.project_id
    )

    dataset_context_records = [
        DatasetContextInDB(
            context_id=context_id,
            dataset_id=dataset_id
        )
        for dataset_id in context_data.dataset_ids
    ]

    automation_context_records = [
        AutomationContextInDB(
            context_id=context_id,
            automation_id=automation_id
        )
        for automation_id in context_data.automation_ids
    ]

    analysis_context_records = [
        AnalysisContextInDB(
            context_id=context_id,
            analysis_id=analysis_id
        )
        for analysis_id in context_data.analysis_ids
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

    return context_record


async def get_context_message(user_id: uuid.UUID, context: Context) -> str:
    datasets = await get_user_datasets_by_ids(user_id, context.dataset_ids)
    # await get_user_automations_by_ids(context.user_id, context.automation_ids)
    automations = []
    analyses = await get_user_analyses_by_ids(user_id, context.analysis_ids)

    context_message = f"""
        <CONTEXT UPDATES>
        Current project in context: {context.project_id}
        Current datasets in context: {datasets}
        Current automations in context: {automations}
        Current analyses in context: {analyses}
        </CONTEXT UPDATES>
        """

    return context_message


async def enter_conversation_mode(conversation_id: uuid.UUID, mode: Literal["chat", "data_integration", "analysis", "automation"]) -> ConversationModeInDB:

    conversation_mode_record = ConversationModeInDB(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        mode=mode,
        created_at=datetime.now(timezone.utc)
    )

    await execute(conversation_mode.insert().values(conversation_mode_record.model_dump()), commit_after=True)

    return conversation_mode_record


async def get_current_conversation_mode(conversation_id: uuid.UUID) -> ConversationModeInDB:

    conversation_mode_record = await fetch_one(
        select(conversation_mode).where(
            conversation_mode.c.conversation_id == conversation_id).order_by(
                conversation_mode.c.created_at.desc())
    )
    return conversation_mode_record
