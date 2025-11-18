import uuid
from datetime import datetime, timezone
from typing import Literal, Optional
from sqlalchemy import select

from synesis_api.modules.orchestrator.schema import (
    ChatMessage,
    Context,
    ContextInDB,
    DataSourceContextInDB,
    DatasetContextInDB,
    PipelineContextInDB,
    AnalysisContextInDB,
    ModelEntityContextInDB,
    ConversationInDB,
    ChatMessageInDB,
    ConversationCreate
)
# from synesis_api.modules.runs.schema import Run
# from kvasir_ontology.main_server.entity_graph import get_entity_graph_description
from synesis_api.modules.orchestrator.models import (
    chat_message,
    conversation,
    chat_context,
    dataset_context,
    pipeline_context,
    analysis_context,
    data_source_context,
    model_instantiated_context,
)
from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.runs.service import create_run
from synesis_api.modules.runs.schema import RunCreate


async def create_conversation(
        conversation_create: ConversationCreate,
        user_id: uuid.UUID,
        name: str,
        conversation_id: Optional[uuid.UUID] = None) -> ConversationInDB:

    conv_id = conversation_id if conversation_id else uuid.uuid4()

    run_record = await create_run(user_id, RunCreate(
        id=uuid.uuid4(),
        type="kvasir",
        run_name="Kvasir run",
        project_id=conversation_create.project_id,
        # conversation_id=conv_id,
        initial_status="waiting"
    ))

    conversation_record = ConversationInDB(
        id=conv_id,
        kvasir_run_id=run_record.id,
        user_id=user_id,
        project_id=conversation_create.project_id,
        name=name,
    )

    await execute(conversation.insert().values(conversation_record.model_dump()), commit_after=True)

    return conversation_record


async def update_conversation_name(conversation_id: uuid.UUID, name: str) -> None:
    await execute(conversation.update().where(conversation.c.id == conversation_id).values(name=name), commit_after=True)


async def get_project_conversations(user_id: uuid.UUID, project_id: uuid.UUID) -> list[ConversationInDB]:
    conversations = await fetch_all(
        select(conversation).where(
            conversation.c.user_id == user_id,
            conversation.c.project_id == project_id
        ).order_by(conversation.c.created_at.desc())
    )

    return [ConversationInDB(**conversation) for conversation in conversations]


async def get_conversation_by_id(conversation_id: uuid.UUID) -> ConversationInDB:
    conversation_record = await fetch_one(
        select(conversation).where(conversation.c.id == conversation_id)
    )
    return ConversationInDB(**conversation_record)


async def get_chat_messages_with_context(conversation_id: uuid.UUID) -> list[ChatMessage]:
    # Get all messages with their contexts in a single query
    query = (
        select(
            chat_message,
            chat_context.c.id.label('ctx_id'),
        )
        .outerjoin(chat_context, chat_message.c.context_id == chat_context.c.id)
        .where(chat_message.c.conversation_id == conversation_id)
        .order_by(chat_message.c.created_at)
    )

    messages_with_context_ids = await fetch_all(query)

    # Get all context IDs to fetch related data in bulk
    context_ids = {msg['ctx_id']
                   for msg in messages_with_context_ids if msg['ctx_id'] is not None}

    context_data = await _get_context_objects_from_ids(list(context_ids))

    chat_messages = []
    for message_data in messages_with_context_ids:
        # Get the context data if context_id exists
        context_obj = next(
            (ctx for ctx in context_data if ctx.id == message_data['ctx_id']), None)

        # Create ChatMessage with full context
        chat_message_obj = ChatMessage(
            **message_data,
            context=context_obj,
        )
        chat_messages.append(chat_message_obj)

    return chat_messages


async def create_chat_message(
        conversation_id: uuid.UUID,
        role: Literal["user", "assistant"],
        content: str,
        type: Literal["tool_call", "chat"],
        context_id: Optional[uuid.UUID] = None,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
) -> ChatMessageInDB:
    # Create the message in database using ChatMessageInDB structure

    chat_message_record = ChatMessageInDB(
        id=id if id else uuid.uuid4(),
        conversation_id=conversation_id,
        role=role,
        type=type,
        content=content,
        context_id=context_id,
        created_at=created_at if created_at else datetime.now(timezone.utc)
    )

    await execute(chat_message.insert().values(chat_message_record.model_dump()), commit_after=True)

    return chat_message_record


async def create_context(context_data: Context) -> Context:
    context_id = uuid.uuid4()

    context_record = ContextInDB(id=context_id)

    data_source_context_records = [
        DataSourceContextInDB(
            context_id=context_id,
            data_source_id=data_source_id
        )
        for data_source_id in context_data.data_source_ids
    ]

    dataset_context_records = [
        DatasetContextInDB(
            context_id=context_id,
            dataset_id=dataset_id
        )
        for dataset_id in context_data.dataset_ids
    ]

    model_instantiated_context_records = [
        ModelEntityContextInDB(
            context_id=context_id,
            model_instantiated_id=model_instantiated_id
        )
        for model_instantiated_id in context_data.model_instantiated_ids
    ]

    pipeline_context_records = [
        PipelineContextInDB(
            context_id=context_id,
            pipeline_id=pipeline_id
        )
        for pipeline_id in context_data.pipeline_ids
    ]

    analysis_context_records = [
        AnalysisContextInDB(
            context_id=context_id,
            analysis_id=analysis_id
        )
        for analysis_id in context_data.analysis_ids
    ]

    if len(dataset_context_records) == 0 and len(pipeline_context_records) == 0 and len(analysis_context_records) == 0 and len(data_source_context_records) == 0 and len(model_instantiated_context_records) == 0:
        raise ValueError("No context records given to create")
    else:
        await execute(chat_context.insert().values(context_record.model_dump()), commit_after=True)

        if len(data_source_context_records) > 0:
            await execute(data_source_context.insert().values([record.model_dump() for record in data_source_context_records]), commit_after=True)
        if len(dataset_context_records) > 0:
            await execute(dataset_context.insert().values([record.model_dump() for record in dataset_context_records]), commit_after=True)
        if len(model_instantiated_context_records) > 0:
            await execute(model_instantiated_context.insert().values([record.model_dump() for record in model_instantiated_context_records]), commit_after=True)
        if len(pipeline_context_records) > 0:
            await execute(pipeline_context.insert().values([record.model_dump() for record in pipeline_context_records]), commit_after=True)
        if len(analysis_context_records) > 0:
            await execute(analysis_context.insert().values([record.model_dump() for record in analysis_context_records]), commit_after=True)

    return context_record


async def _get_context_objects_from_ids(context_ids: list[uuid.UUID]) -> list[Context]:

    context_data = []

    data_source_contexts = await fetch_all(
        select(data_source_context).where(
            data_source_context.c.context_id.in_(context_ids))
    )

    dataset_contexts = await fetch_all(
        select(dataset_context).where(
            dataset_context.c.context_id.in_(context_ids))
    )

    pipeline_contexts = await fetch_all(
        select(pipeline_context).where(
            pipeline_context.c.context_id.in_(context_ids))
    )

    analysis_contexts = await fetch_all(
        select(analysis_context).where(
            analysis_context.c.context_id.in_(context_ids))
    )

    model_instantiated_contexts = await fetch_all(
        select(model_instantiated_context).where(
            model_instantiated_context.c.context_id.in_(context_ids))
    )

    for ctx_id in context_ids:
        data_source_ids = [dc['data_source_id']
                           for dc in data_source_contexts if dc['context_id'] == ctx_id]
        dataset_ids = [dc['dataset_id']
                       for dc in dataset_contexts if dc['context_id'] == ctx_id]
        pipeline_ids = [ac['pipeline_id']
                        for ac in pipeline_contexts if ac['context_id'] == ctx_id]
        analysis_ids = [ac['analysis_id']
                        for ac in analysis_contexts if ac['context_id'] == ctx_id]
        model_instantiated_ids = [ac['model_instantiated_id']
                                  for ac in model_instantiated_contexts if ac['context_id'] == ctx_id]

        context_data.append(Context(
            id=ctx_id,
            data_source_ids=data_source_ids,
            dataset_ids=dataset_ids,
            pipeline_ids=pipeline_ids,
            analysis_ids=analysis_ids,
            model_instantiated_ids=model_instantiated_ids
        ))

    return context_data
