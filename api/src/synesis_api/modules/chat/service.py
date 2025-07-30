import uuid
from datetime import datetime, timezone
from typing import Literal, Optional
from sqlalchemy import select, func
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from synesis_api.modules.chat.schema import (
    ChatMessage,
    PydanticMessageInDB,
    ConversationWithMessages,
    Context,
    ContextInDB,
    DatasetContextInDB,
    AutomationContextInDB,
    AnalysisContextInDB,
    ConversationInDB,
    ConversationModeInDB,
    Conversation)
from synesis_api.modules.chat.models import (
    chat_message,
    chat_pydantic_message,
    conversation,
    context,
    dataset_context,
    automation_context, analysis_context, conversation_mode)
from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.data_objects.service import get_user_datasets_by_ids
from synesis_api.modules.analysis.service import get_user_analyses_by_ids


async def create_conversation(conversation_id: uuid.UUID, project_id: uuid.UUID, user_id: uuid.UUID, name: str) -> ConversationInDB:
    conversation_record = ConversationInDB(
        id=conversation_id,
        user_id=user_id,
        project_id=project_id,
        name=name,
    )
    await execute(conversation.insert().values(conversation_record.model_dump()), commit_after=True)

    await enter_conversation_mode(conversation_id, "chat")

    return conversation_record


async def get_conversations(user_id: uuid.UUID) -> list[Conversation]:
    # Use a subquery to get the latest mode for each conversation
    latest_modes = (
        select(
            conversation_mode.c.conversation_id,
            conversation_mode.c.mode,
            func.row_number().over(
                partition_by=conversation_mode.c.conversation_id,
                order_by=conversation_mode.c.created_at.desc()
            ).label('rn')
        )
        .subquery()
    )

    # Join conversations with their latest modes
    query = (
        select(conversation, latest_modes.c.mode)
        .outerjoin(latest_modes, conversation.c.id == latest_modes.c.conversation_id)
        .where(
            conversation.c.user_id == user_id,
            (latest_modes.c.rn == 1) | (latest_modes.c.rn.is_(None))
        )
    )

    results = await fetch_all(query)

    conversation_list = []
    for result in results:
        conversation_data = {k: v for k,
                             v in result.items() if k in conversation.columns}
        mode = result.get('mode', 'chat')  # Default to 'chat' if no mode found

        conversation_record = Conversation(
            **conversation_data,
            mode=mode
        )
        conversation_list.append(conversation_record)

    return conversation_list


async def get_conversation(conversation_id: uuid.UUID) -> ConversationWithMessages:
    """Get a single conversation with its messages"""
    # Get conversation with latest mode
    latest_mode = (
        select(
            conversation_mode.c.mode,
            conversation_mode.c.conversation_id,
            func.row_number().over(
                partition_by=conversation_mode.c.conversation_id,
                order_by=conversation_mode.c.created_at.desc()
            ).label('rn')
        )
        .where(conversation_mode.c.conversation_id == conversation_id)
        .subquery()
    )

    query = (
        select(conversation, latest_mode.c.mode)
        .outerjoin(latest_mode, conversation.c.id == latest_mode.c.conversation_id)
        .where(
            conversation.c.id == conversation_id,
            (latest_mode.c.rn == 1) | (latest_mode.c.rn.is_(None))
        )
    )

    result = await fetch_one(query)

    if not result:
        return None

    conversation_data = {k: v for k,
                         v in result.items() if k in conversation.columns}
    mode = result.get('mode', 'chat')

    # Get messages for this conversation
    messages = await get_messages(conversation_id)

    # Create ConversationWithMessages object
    conversation_record = ConversationWithMessages(
        **conversation_data,
        messages=messages,
        mode=mode
    )

    return conversation_record


async def get_messages(conversation_id: uuid.UUID) -> list[ChatMessage]:
    # Get all messages with their contexts in a single query
    query = (
        select(
            chat_message,
            context.c.id.label('ctx_id'),
        )
        .outerjoin(context, chat_message.c.context_id == context.c.id)
        .where(chat_message.c.conversation_id == conversation_id)
        .order_by(chat_message.c.created_at)
    )

    messages_with_contexts = await fetch_all(query)

    # Get all context IDs to fetch related data in bulk
    context_ids = {msg['ctx_id']
                   for msg in messages_with_contexts if msg['ctx_id'] is not None}

    # Fetch all related context data in bulk
    context_data = {}
    if context_ids:
        # Get dataset contexts
        dataset_contexts = await fetch_all(
            select(dataset_context).where(
                dataset_context.c.context_id.in_(context_ids))
        )

        # Get automation contexts
        automation_contexts = await fetch_all(
            select(automation_context).where(
                automation_context.c.context_id.in_(context_ids))
        )

        # Get analysis contexts
        analysis_contexts = await fetch_all(
            select(analysis_context).where(
                analysis_context.c.context_id.in_(context_ids))
        )

        # Group by context_id
        for ctx_id in context_ids:
            dataset_ids = [dc['dataset_id']
                           for dc in dataset_contexts if dc['context_id'] == ctx_id]
            automation_ids = [ac['automation_id']
                              for ac in automation_contexts if ac['context_id'] == ctx_id]
            analysis_ids = [ac['analysis_id']
                            for ac in analysis_contexts if ac['context_id'] == ctx_id]

            context_data[ctx_id] = Context(
                id=ctx_id,
                dataset_ids=dataset_ids,
                automation_ids=automation_ids,
                analysis_ids=analysis_ids
            )

    chat_messages = []
    for message_data in messages_with_contexts:
        # Get the context data if context_id exists
        context_obj = context_data.get(
            message_data['ctx_id']) if message_data['ctx_id'] else None

        # Create ChatMessage with full context
        chat_message_obj = ChatMessage(
            id=message_data['id'],
            conversation_id=message_data['conversation_id'],
            role=message_data['role'],
            type=message_data['type'],
            job_id=message_data['job_id'],
            content=message_data['content'],
            context=context_obj,
            created_at=message_data['created_at']
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
        dataset_ids=dataset_ids,
        automation_ids=automation_ids,
        analysis_ids=analysis_ids
    )


async def get_messages_pydantic(conversation_id: uuid.UUID) -> list[ModelMessage]:
    c = await fetch_all(
        select(chat_pydantic_message).where(
            chat_pydantic_message.c.conversation_id == conversation_id)
    )
    messages: list[ModelMessage] = []
    for message in c:
        messages.extend(
            ModelMessagesTypeAdapter.validate_json(message["message_list"]))

    return messages


async def create_message(
        conversation_id: uuid.UUID,
        role: Literal["user", "agent"],
        content: str,
        type: Literal["tool_call", "result", "error", "chat"],
        job_id: Optional[uuid.UUID] = None,
        context_id: Optional[uuid.UUID] = None,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
) -> ChatMessage:
    # Create the message in database using ChatMessageInDB structure

    message_data = {
        "id": id if id else uuid.uuid4(),
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "type": type,
        "job_id": job_id,
        "context_id": context_id,
        "created_at": created_at if created_at else datetime.now(timezone.utc)
    }

    await execute(chat_message.insert().values(message_data), commit_after=True)

    # Get the full context if context_id exists
    context_obj = None
    if context_id:
        context_obj = await get_context_by_id(context_id)

    # Return the full ChatMessage with context
    return ChatMessage(
        id=message_data["id"],
        conversation_id=conversation_id,
        role=role,
        type=type,
        job_id=job_id,
        content=content,
        context=context_obj,
        created_at=message_data["created_at"]
    )


async def create_messages_pydantic(conversation_id: uuid.UUID, messages: bytes) -> PydanticMessageInDB:
    message = PydanticMessageInDB(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        message_list=messages,
        created_at=datetime.now(timezone.utc)
    )
    await execute(chat_pydantic_message.insert().values(message.model_dump()), commit_after=True)
    return message


async def create_context(
        context_data: Context
) -> Context:
    context_id = uuid.uuid4()

    context_record = ContextInDB(
        id=context_id,
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
    """Get the current mode for a conversation (most recent mode)"""
    conversation_mode_record = await fetch_one(
        select(conversation_mode).where(
            conversation_mode.c.conversation_id == conversation_id
        ).order_by(conversation_mode.c.created_at.desc())
    )

    conversation_mode_record = ConversationModeInDB(
        id=conversation_mode_record["id"],
        conversation_id=conversation_mode_record["conversation_id"],
        mode=conversation_mode_record["mode"],
        created_at=conversation_mode_record["created_at"]
    )

    return conversation_mode_record
