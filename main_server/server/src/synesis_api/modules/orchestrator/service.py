import uuid
from datetime import datetime, timezone
from typing import Literal, Optional, List
from sqlalchemy import select
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from synesis_schemas.main_server import (
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
    ChatPydanticMessageInDB,
    ConversationCreate,
    ProjectGraph,
    DataSourceInGraph,
    DatasetInGraph,
    PipelineInGraph,
    AnalysisInGraph,
    ModelEntityInGraph,
    DatasetFull,
    PipelineFull,
    ModelEntityFull,
    DataSourceFull
)

from synesis_api.modules.orchestrator.models import (
    chat_message,
    chat_pydantic_message,
    conversation,
    chat_context,
    dataset_context,
    pipeline_context,
    analysis_context,
    data_source_context,
    model_entity_context,
)
from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.data_objects.service import get_user_datasets_by_ids, get_project_datasets
# from synesis_api.modules.analysis.service import get_user_analyses_by_ids
from synesis_api.modules.data_sources.service import get_data_sources, get_project_data_sources
from synesis_api.modules.pipeline.service import get_user_pipelines_by_ids, get_project_pipelines
from synesis_api.modules.model.service import get_user_model_entities_by_ids, get_project_model_entities


async def create_conversation(
        conversation_create: ConversationCreate,
        user_id: uuid.UUID,
        name: str,
        conversation_id: Optional[uuid.UUID] = None) -> ConversationInDB:

    conversation_record = ConversationInDB(
        id=conversation_id if conversation_id else uuid.uuid4(),
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
            id=message_data['id'],
            conversation_id=message_data['conversation_id'],
            role=message_data['role'],
            content=message_data['content'],
            created_at=message_data['created_at'],
            context=context_obj,
        )
        chat_messages.append(chat_message_obj)

    return chat_messages


async def get_chat_messages_pydantic(conversation_id: uuid.UUID) -> list[ModelMessage]:
    c = await fetch_all(
        select(chat_pydantic_message).where(
            chat_pydantic_message.c.conversation_id == conversation_id)
    )
    messages: list[ModelMessage] = []
    for message in c:
        messages.extend(
            ModelMessagesTypeAdapter.validate_json(message["message_list"]))

    return messages


async def create_chat_message(
        conversation_id: uuid.UUID,
        role: Literal["user", "assistant"],
        content: str,
        context_id: Optional[uuid.UUID] = None,
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
) -> ChatMessage:
    # Create the message in database using ChatMessageInDB structure

    chat_message_record = ChatMessageInDB(
        id=id if id else uuid.uuid4(),
        conversation_id=conversation_id,
        role=role,
        content=content,
        context_id=context_id,
        created_at=created_at if created_at else datetime.now(timezone.utc)
    )

    await execute(chat_message.insert().values(chat_message_record.model_dump()), commit_after=True)

    return chat_message_record


async def create_chat_message_pydantic(conversation_id: uuid.UUID, messages: List[bytes]) -> List[ChatPydanticMessageInDB]:
    chat_pydantic_message_records = [ChatPydanticMessageInDB(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        message_list=message,
        created_at=datetime.now(timezone.utc)
    ) for message in messages]

    await execute(chat_pydantic_message.insert().values([record.model_dump() for record in chat_pydantic_message_records]), commit_after=True)

    return chat_pydantic_message_records


async def create_context(
        context_data: Context
) -> Context:
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

    model_entity_context_records = [
        ModelEntityContextInDB(
            context_id=context_id,
            model_entity_id=model_entity_id
        )
        for model_entity_id in context_data.model_entity_ids
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

    if len(dataset_context_records) == 0 and len(pipeline_context_records) == 0 and len(analysis_context_records) == 0 and len(data_source_context_records) == 0 and len(model_entity_context_records) == 0:
        raise ValueError("No context records given to create")
    else:
        await execute(chat_context.insert().values(context_record.model_dump()), commit_after=True)

        if len(data_source_context_records) > 0:
            await execute(data_source_context.insert().values([record.model_dump() for record in data_source_context_records]), commit_after=True)
        if len(dataset_context_records) > 0:
            await execute(dataset_context.insert().values([record.model_dump() for record in dataset_context_records]), commit_after=True)
        if len(model_entity_context_records) > 0:
            await execute(model_entity_context.insert().values([record.model_dump() for record in model_entity_context_records]), commit_after=True)
        if len(pipeline_context_records) > 0:
            await execute(pipeline_context.insert().values([record.model_dump() for record in pipeline_context_records]), commit_after=True)
        if len(analysis_context_records) > 0:
            await execute(analysis_context.insert().values([record.model_dump() for record in analysis_context_records]), commit_after=True)

    return context_record


async def get_context_message(user_id: uuid.UUID, context: Context) -> str:
    datasets = []
    data_sources = []
    pipelines = []
    analyses = []
    model_entities = []

    if len(context.dataset_ids) > 0:
        datasets = await get_user_datasets_by_ids(user_id, context.dataset_ids, max_features=20)
    if len(context.data_source_ids) > 0:
        data_sources = await get_data_sources(context.data_source_ids)
    if len(context.pipeline_ids) > 0:
        pipelines = await get_user_pipelines_by_ids(user_id, context.pipeline_ids)
    if len(context.analysis_ids) > 0:
        # analyses = await get_user_analyses_by_ids(user_id, context.analysis_ids)
        analyses = []
    if len(context.model_entity_ids) > 0:
        model_entities = await get_user_model_entities_by_ids(context.model_entity_ids)

    context_message = f"""
        <CONTEXT UPDATES>
        Data sources in context: {data_sources}
        Datasets in context: {datasets}
        Pipelines in context: {pipelines}
        Analyses in context: {analyses}
        Model entities in context: {model_entities}
        </CONTEXT UPDATES>
        """

    return context_message


async def get_project_graph(user_id: uuid.UUID, project_id: uuid.UUID) -> ProjectGraph:
    data_sources = await get_project_data_sources(user_id, project_id)
    datasets = await get_project_datasets(user_id, project_id, include_features=False)
    pipelines = await get_project_pipelines(user_id, project_id)
    analyses = []  # await get_project_analyses(project_id)
    model_entities = await get_project_model_entities(project_id)

    def _get_data_sources_in_graph(data_sources: List[DataSourceFull], datasets: List[DatasetFull]) -> List[DataSourceInGraph]:
        objs = []
        for ds in data_sources:
            output_dataset_ids = [
                dset.id for dset in datasets if ds.id in dset.sources.data_source_ids]
            output_analysis_ids = []
            objs.append(DataSourceInGraph(
                id=ds.id,
                name=ds.name,
                type=ds.type,
                brief_description=f"{ds.name} {ds.type} data source",
                to_datasets=output_dataset_ids,
                to_analyses=output_analysis_ids
            ))
        return objs

    def _get_datasets_in_graph(datasets: List[DatasetFull], pipelines: List[PipelineFull]) -> List[DatasetInGraph]:
        objs = []
        for ds in datasets:
            output_pipeline_ids = [
                p.id for p in pipelines if ds.id in p.sources.dataset_ids]
            output_analysis_ids = []

            objs.append(DatasetInGraph(
                id=ds.id,
                name=ds.name,
                brief_description=ds.description,
                to_pipelines=output_pipeline_ids,
                to_analyses=output_analysis_ids,
                from_data_sources=ds.sources.data_source_ids,
                from_datasets=ds.sources.dataset_ids,
                from_pipelines=ds.sources.pipeline_ids
            ))
        return objs

    def _get_pipelines_in_graph(pipelines: List[PipelineFull], datasets: List[DatasetFull], model_entities: List[ModelEntityFull]) -> List[PipelineInGraph]:
        objs = []
        for p in pipelines:
            output_dataset_ids = [
                ds.id for ds in datasets if p.id in ds.sources.pipeline_ids]
            output_model_entity_ids = [
                me.id for me in model_entities if p.id == me.pipeline_id]

            objs.append(PipelineInGraph(
                id=p.id,
                name=p.name,
                brief_description=p.description,
                from_datasets=p.sources.dataset_ids,
                from_model_entities=p.sources.model_entity_ids,
                to_datasets=output_dataset_ids,
                to_model_entities=output_model_entity_ids
            ))
        return objs

    def _get_analyses_in_graph() -> List[AnalysisInGraph]:
        return []

    def _get_model_entities_in_graph(model_entities: List[ModelEntityFull], pipelines: List[PipelineFull]) -> List[ModelEntityInGraph]:
        objs = []
        for me in model_entities:
            output_pipeline_ids = [
                p.id for p in pipelines if me.id in p.sources.model_entity_ids]
            objs.append(ModelEntityInGraph(
                id=me.id,
                name=me.name,
                brief_description=me.description,
                to_pipelines=output_pipeline_ids,
            ))
        return objs

    data_sources_in_graph = _get_data_sources_in_graph(data_sources, datasets)
    datasets_in_graph = _get_datasets_in_graph(datasets, pipelines)
    pipelines_in_graph = _get_pipelines_in_graph(
        pipelines, datasets, model_entities)
    analyses_in_graph = _get_analyses_in_graph()
    model_entities_in_graph = _get_model_entities_in_graph(
        model_entities, pipelines)

    return ProjectGraph(
        data_sources=data_sources_in_graph,
        datasets=datasets_in_graph,
        pipelines=pipelines_in_graph,
        analyses=analyses_in_graph,
        model_entities=model_entities_in_graph
    )


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

    model_entity_contexts = await fetch_all(
        select(model_entity_context).where(
            model_entity_context.c.context_id.in_(context_ids))
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
        model_entity_ids = [ac['model_entity_id']
                            for ac in model_entity_contexts if ac['context_id'] == ctx_id]

        context_data.append(Context(
            id=ctx_id,
            data_source_ids=data_source_ids,
            dataset_ids=dataset_ids,
            pipeline_ids=pipeline_ids,
            analysis_ids=analysis_ids,
            model_entity_ids=model_entity_ids
        ))

    return context_data
