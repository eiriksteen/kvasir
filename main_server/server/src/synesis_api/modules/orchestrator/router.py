import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Annotated, List

from synesis_schemas.main_server import (
    ChatMessage,
    UserChatMessageCreate,
    ChatMessageInDB,
    ConversationInDB,
    ConversationCreate,
    ProjectGraph,
    RunCreate,
    RunSpecificationCreate,
    ContextCreate,
    ContextInDB,
)
from synesis_schemas.main_server.runs import Run
from synesis_api.modules.orchestrator.service import (
    create_conversation,
    get_chat_messages_pydantic,
    create_chat_message,
    get_project_conversations,
    create_context,
    create_chat_message_pydantic,
    get_context_message,
    get_chat_messages_with_context,
    get_conversation_by_id,
    update_conversation_name,
    get_project_graph
)
from synesis_api.modules.orchestrator.agent import orchestrator_agent
from synesis_api.modules.orchestrator.agent.output import (
    NoHandoffOutput,
    DataIntegrationRunDescriptionOutput,
    PipelineRunDescriptionOutput,
    ModelIntegrationRunDescriptionOutput,
    AnalysisHandoffOutput
)
from synesis_api.modules.runs.service import create_run
from synesis_api.auth.service import get_current_user, user_owns_conversation
from synesis_schemas.main_server import User
from synesis_api.auth.service import oauth2_scheme
from synesis_api.client import MainServerClient, post_run_analysis
from synesis_schemas.project_server import RunAnalysisRequest
from synesis_api.modules.orchestrator.agent.deps import OrchestatorAgentDeps


router = APIRouter()


# This endpoint may launch agent runs
# The frontend should listen to the runs sse endpoint to listen for when this happens
# Then, the messages/{run_id} can be used to listen to the messages
@router.post("/completions")
async def post_chat(
    prompt: UserChatMessageCreate,
    user: Annotated[User, Depends(get_current_user)] = None,
    token: str = Depends(oauth2_scheme)
) -> StreamingResponse:

    conversation_record = await get_conversation_by_id(prompt.conversation_id)

    if not conversation_record.user_id == user.id:
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")

    messages = await get_chat_messages_pydantic(prompt.conversation_id)

    is_new_conversation = len(messages) == 0

    # TODO: Important to optimize this, as it will blow up the context with repeated messages!
    # One option is to keep the full entity objects just for the current context, and collapse to the IDs and names for the past ones
    context_message = await get_context_message(user.id, prompt.context)
    project_graph = await get_project_graph(user.id, conversation_record.project_id)

    orchestrator_run = await orchestrator_agent.run(
        f"The user prompt is: '{prompt.content}'. \n\n" +
        "Decide whether to launch an agent or just respond directly to the prompt. \n\n" +
        "If launching an agent, choose between 'analysis', 'data_integration' or 'pipeline'. If not just choose no handoff. \n\n"
        f"The context is:\n\n{context_message}\n\n" +
        f"The project graph is:\n\n{project_graph.model_dump_json()}",
        output_type=[NoHandoffOutput,
                     AnalysisHandoffOutput,
                     PipelineRunDescriptionOutput,
                     DataIntegrationRunDescriptionOutput,
                     ModelIntegrationRunDescriptionOutput],
        deps=OrchestatorAgentDeps(
            user_id=user.id,
            project_id=conversation_record.project_id
        ),
        message_history=messages
    )

    async def stream_response():

        response_message = ChatMessageInDB(
            id=uuid.uuid4(),
            conversation_id=conversation_record.id,
            role="assistant",
            content="",
            context_id=None,
            created_at=datetime.now(timezone.utc)
        )

        context_in_db = None
        if prompt.context and len(prompt.context.data_source_ids) + len(prompt.context.dataset_ids) + len(prompt.context.pipeline_ids) + len(prompt.context.analysis_ids) > 0:
            context_in_db = await create_context(prompt.context)
            response_message.context_id = context_in_db.id

        async with orchestrator_agent.run_stream(
            "Now respond to the user! If you launched an agent, explain what you did. If not, just respond directly to the user prompt.",
            output_type=str,
            deps=OrchestatorAgentDeps(
                user_id=user.id,
                project_id=conversation_record.project_id
            ),
            message_history=messages+orchestrator_run.new_messages()
        ) as result:
            prev_text = ""
            async for text in result.stream_output(debounce_by=0.01):
                if text != prev_text:
                    response_message.content = text
                    yield f"data: {response_message.model_dump_json(by_alias=True)}\n\n"
                    prev_text = text

        await create_chat_message(
            conversation_record.id,
            "user",
            prompt.content,
            context_id=context_in_db.id if context_in_db else None
        )
        await create_chat_message(conversation_record.id, "assistant", response_message.content, response_message.context_id, response_message.id)
        await create_chat_message_pydantic(conversation_record.id, [orchestrator_run.new_messages_json(), result.new_messages_json()])

        print("THE ORCHESTRATOR RUN OUTPUT", orchestrator_run.output)

        # client = MainServerClient(token)
        if not isinstance(orchestrator_run.output, NoHandoffOutput):
            client = MainServerClient(token)

            if isinstance(orchestrator_run.output, AnalysisHandoffOutput):

                analysis_request = RunAnalysisRequest(
                    project_id=conversation_record.project_id,
                    dataset_ids=prompt.context.dataset_ids,
                    automation_ids=[],  # prompt.context.automation_ids,
                    analysis_ids=prompt.context.analysis_ids,
                    prompt=prompt.content,
                    user_id=user.id,
                    message_history=messages,
                    conversation_id=prompt.conversation_id,
                    context_message=context_message,
                    run_id=None
                )

                await post_run_analysis(client, analysis_request)

            if isinstance(orchestrator_run.output, DataIntegrationRunDescriptionOutput):
                await create_run(
                    user.id,
                    RunCreate(
                        type="data_integration",
                        project_id=conversation_record.project_id,
                        conversation_id=conversation_record.id,
                        data_sources_in_run=orchestrator_run.output.data_source_ids,
                        datasets_in_run=orchestrator_run.output.dataset_ids,
                        spec=RunSpecificationCreate(
                            run_name=orchestrator_run.output.run_name,
                            plan_and_deliverable_description_for_agent=orchestrator_run.output.plan_and_deliverable_description_for_agent,
                            plan_and_deliverable_description_for_user=orchestrator_run.output.plan_and_deliverable_description_for_user,
                            questions_for_user=orchestrator_run.output.questions_for_user)
                    ))

            elif isinstance(orchestrator_run.output, PipelineRunDescriptionOutput):
                await create_run(
                    user.id,
                    RunCreate(
                        type="pipeline",
                        project_id=conversation_record.project_id,
                        conversation_id=conversation_record.id,
                        datasets_in_run=orchestrator_run.output.input_dataset_ids,
                        model_entities_in_run=orchestrator_run.output.input_model_entity_ids,
                        spec=RunSpecificationCreate(
                            run_name=orchestrator_run.output.run_name,
                            plan_and_deliverable_description_for_agent=orchestrator_run.output.plan_and_deliverable_description_for_agent,
                            plan_and_deliverable_description_for_user=orchestrator_run.output.plan_and_deliverable_description_for_user,
                            questions_for_user=orchestrator_run.output.questions_for_user,
                            configuration_defaults_description=orchestrator_run.output.configuration_defaults_description)
                    ))

            elif isinstance(orchestrator_run.output, ModelIntegrationRunDescriptionOutput):
                await create_run(
                    user.id,
                    RunCreate(
                        type="model_integration",
                        project_id=conversation_record.project_id,
                        conversation_id=conversation_record.id,
                        spec=RunSpecificationCreate(
                            run_name=orchestrator_run.output.run_name,
                            plan_and_deliverable_description_for_agent=orchestrator_run.output.plan_and_deliverable_description_for_agent,
                            plan_and_deliverable_description_for_user=orchestrator_run.output.plan_and_deliverable_description_for_user,
                            questions_for_user=orchestrator_run.output.questions_for_user
                        )
                    )
                )

        if is_new_conversation:
            name = await orchestrator_agent.run(
                f"The user wants to start a new conversation. The user has written this: '{prompt.content}'.\n\n" +
                "What is the name of the conversation? Just give me the name of the conversation, no other text.\n\n" +
                "NB: Do not output a response to the prompt, that is done elsewhere! Just produce a suitable topic name given the prompt.",
                output_type=str
            )
            name = name.output.replace('"', '').replace("'", "").strip()

            await update_conversation_name(conversation_record.id, name)

        success_message = ChatMessageInDB(
            id=uuid.uuid4(),
            conversation_id=conversation_record.id,
            role="assistant",
            content="DONE",
            context_id=None,
            created_at=datetime.now(timezone.utc)
        )

        yield f"data: {success_message.model_dump_json(by_alias=True)}\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")


@router.post("/conversation")
async def post_user_conversation(conversation_data: ConversationCreate, user: Annotated[User, Depends(get_current_user)] = None) -> ConversationInDB:
    conversation_record = await create_conversation(conversation_data, user.id, "New Chat")
    return conversation_record


@router.get("/messages/{conversation_id}")
async def fetch_messages(
        conversation_id: uuid.UUID,
        user: Annotated[User, Depends(get_current_user)] = None) -> List[ChatMessage]:
    if not await user_owns_conversation(user.id, conversation_id):
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")

    messages = await get_chat_messages_with_context(conversation_id)

    return messages


@router.get("/project-conversations/{project_id}")
async def fetch_project_conversations(project_id: uuid.UUID, user: Annotated[User, Depends(get_current_user)] = None) -> List[ConversationInDB]:
    conversations = await get_project_conversations(user.id, project_id)
    return conversations


@router.get("/project-graph/{project_id}")
async def fetch_project_graph(project_id: uuid.UUID, user: Annotated[User, Depends(get_current_user)] = None) -> ProjectGraph:
    graph = await get_project_graph(user.id, project_id)
    return graph


@router.post("/chat-message-pydantic/{conversation_id}")
async def create_chat_message_pydantic_endpoint(
    conversation_id: uuid.UUID,
    messages: List[bytes],
    user: Annotated[User, Depends(get_current_user)] = None
):
    if not await user_owns_conversation(user.id, conversation_id):
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")

    result = await create_chat_message_pydantic(conversation_id, messages)
    return result


@router.post("/context")
async def create_context_endpoint(
    context: ContextCreate,
    user: Annotated[User, Depends(get_current_user)] = None
) -> ContextInDB:
    result = await create_context(context)
    return result
