import uuid
import asyncio
import logging
from pydantic_ai.agent import Agent
from pydantic_ai.messages import FunctionToolCallEvent
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
    User,
    ImplementationApprovalResponse,
    # ContextCreate,
    # ContextInDB,
)
from synesis_schemas.project_server import ImplementationSummary
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
    get_run_status_message,
    get_project_description_message
)
from synesis_api.modules.orchestrator.agent import orchestrator_agent, orchestrator_toolset
from synesis_api.auth.service import get_current_user, user_owns_conversation
from synesis_api.modules.orchestrator.agent.deps import OrchestratorAgentDeps
from synesis_api.app_secrets import SSE_MIN_SLEEP_TIME


logger = logging.getLogger(__name__)
router = APIRouter()


# This endpoint may launch agent runs
# The frontend should listen to the runs sse endpoint to listen for when this happens
# Then, the messages/{run_id} can be used to listen to the messages
@router.post("/completions")
async def post_chat(
    prompt: UserChatMessageCreate,
    user: Annotated[User, Depends(get_current_user)] = None
) -> StreamingResponse:

    # TODO: Add support for open connection with analysis, and add rejected status to a run so we don't keep monitoring it

    conversation_record = await get_conversation_by_id(prompt.conversation_id)

    if not conversation_record.user_id == user.id:
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")

    messages = await get_chat_messages_pydantic(prompt.conversation_id)
    context_message = await get_context_message(user.id, prompt.context)
    project_graph_message = await get_project_description_message(user.id, conversation_record.project_id)
    runs_status_message = await get_run_status_message(user.id, prompt.conversation_id)

    is_new_conversation = len(messages) == 0

    async def stream_response():

        plan_response_message = ChatMessageInDB(
            id=uuid.uuid4(),
            conversation_id=conversation_record.id,
            role="assistant",
            type="chat",
            content="",
            context_id=None,
            created_at=datetime.now(timezone.utc)
        )

        result_response_message = ChatMessageInDB(
            id=uuid.uuid4(),
            conversation_id=conversation_record.id,
            role="assistant",
            type="chat",
            content="",
            context_id=None,
            created_at=datetime.now(timezone.utc)
        )

        context_in_db = None
        if prompt.context and len(prompt.context.data_source_ids) + len(prompt.context.dataset_ids) + len(prompt.context.pipeline_ids) + len(prompt.context.analysis_ids) > 0:
            context_in_db = await create_context(prompt.context)
            plan_response_message.context_id = context_in_db.id
            result_response_message.context_id = context_in_db.id
        context_id = context_in_db.id if context_in_db else None

        # Build the initial prompt with all context information
        initial_prompt = (
            f"The user just submitted the following prompt:\n\n{prompt.content}\n\n" +
            f"The context is:\n\n{context_message}\n\n" +
            f"The project graph is:\n\n{project_graph_message}\n\n" +
            f"The runs status message is:\n\n{runs_status_message}\n\n" +
            "First, respond to the user explaining what you plan to do. " +
            "If you need to launch an agent (analysis, data_integration, pipeline, or model_integration), explain what you will do. " +
            "If a run just changed state, let the user know and explain the next steps. " +
            "Otherwise, just respond directly to the user prompt. " +
            "Do not call any tools here, just describe what you will do. "
        )

        deps = OrchestratorAgentDeps(
            user_id=user.id,
            project_id=conversation_record.project_id,
            conversation_id=conversation_record.id
        )

        # Stream the response first to minimize perceived latency
        async with orchestrator_agent.run_stream(
            initial_prompt,
            output_type=str,
            deps=deps,
            message_history=messages
        ) as plan_run:
            prev_plan_text = ""
            async for plan_text in plan_run.stream_output(debounce_by=0.01):
                if plan_text != prev_plan_text:
                    plan_response_message.content = plan_text
                    yield f"data: {plan_response_message.model_dump_json(by_alias=True)}\n\n"
                    prev_plan_text = plan_text

        # Immediately save since the orchestrator run can take a little time
        if prompt.save_to_db:
            await create_chat_message(
                conversation_record.id,
                "user",
                prompt.content,
                context_id=context_id,
                type="chat"
            )

        await create_chat_message(
            conversation_record.id,
            "assistant",
            plan_response_message.content,
            type="chat",
            context_id=context_id,
            id=plan_response_message.id
        )

        async with orchestrator_agent.iter(
            "Now decide whether to launch an agent, call some other tools, or just respond directly. " +
            "Please limit yourself to one agent launch at a time, unless it really makes sense to parallelize. " +
            "The output is a bool indicating whether you would like to explain the results of your run. " +
            "The default should be False, but if there were any results the user should know about, output True. " +
            "If you successfully launched an agent, output False! The user will automatically see the specification for the run. " +
            "Output True if the user asked question where you needed a tool call to answer it, as we will need to explain the results to the user. ",
            output_type=bool,
            deps=deps,
            message_history=messages+plan_run.new_messages(),
            toolsets=[orchestrator_toolset]
        ) as orchestator_run:
            async for node in orchestator_run:
                if Agent.is_call_tools_node(node):
                    async with node.stream(orchestator_run.ctx) as handle_stream:
                        async for event in handle_stream:
                            if isinstance(event, FunctionToolCallEvent):
                                tool_call_message = await create_chat_message(
                                    conversation_record.id,
                                    "assistant",
                                    f"Calling {event.part.tool_name}",
                                    type="tool_call",
                                    context_id=context_id
                                )
                                yield f"data: {tool_call_message.model_dump_json(by_alias=True)}\n\n"

        all_messages_pydantic = [
            plan_run.new_messages_json(),
            orchestator_run.result.new_messages_json()
        ]

        if orchestator_run.result.output:
            async with orchestrator_agent.run_stream(
                "Now explain the results of your run.",
                output_type=str,
                deps=deps,
                message_history=messages+plan_run.new_messages()+orchestator_run.result.new_messages()
            ) as result_run:
                prev_result_text = ""
                async for result_text in result_run.stream_output(debounce_by=0.01):
                    if result_text != prev_result_text:
                        result_response_message.content = result_text
                        yield f"data: {result_response_message.model_dump_json(by_alias=True)}\n\n"
                        prev_result_text = result_text

            all_messages_pydantic.append(result_run.new_messages_json())

            if result_response_message.content:
                await create_chat_message(
                    conversation_record.id,
                    "assistant",
                    result_response_message.content,
                    type="chat",
                    context_id=context_id,
                    id=result_response_message.id
                )

        await create_chat_message_pydantic(conversation_record.id, all_messages_pydantic)

        if is_new_conversation:
            name = await orchestrator_agent.run(
                f"The user wants to start a new conversation. The user has written this: '{prompt.content}'.\n\n" +
                "What is the name of the conversation? Just give me the name of the conversation, no other text.\n\n" +
                "NB: Do not output a response to the prompt, that is done elsewhere! Just produce a suitable topic name given the prompt.",
                output_type=str
            )
            name = name.output.replace(
                '"', '').replace("'", "").strip()

            await update_conversation_name(conversation_record.id, name)

        success_message = ChatMessageInDB(
            id=uuid.uuid4(),
            conversation_id=conversation_record.id,
            role="assistant",
            type="chat",
            content="DONE",
            context_id=None,
            created_at=datetime.now(timezone.utc)
        )

        yield f"data: {success_message.model_dump_json(by_alias=True)}\n\n"

        await asyncio.sleep(SSE_MIN_SLEEP_TIME)

    return StreamingResponse(stream_response(), media_type="text/event-stream")


@router.post("/conversation", response_model=ConversationInDB)
async def post_user_conversation(conversation_data: ConversationCreate, user: Annotated[User, Depends(get_current_user)] = None) -> ConversationInDB:
    conversation_record = await create_conversation(conversation_data, user.id, "New Chat")
    return conversation_record


@router.get("/messages/{conversation_id}", response_model=List[ChatMessage])
async def fetch_messages(
        conversation_id: uuid.UUID,
        user: Annotated[User, Depends(get_current_user)] = None) -> List[ChatMessage]:
    if not await user_owns_conversation(user.id, conversation_id):
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")

    messages = await get_chat_messages_with_context(conversation_id)

    return messages


@router.get("/project-conversations/{project_id}", response_model=List[ConversationInDB])
async def fetch_project_conversations(project_id: uuid.UUID, user: Annotated[User, Depends(get_current_user)] = None) -> List[ConversationInDB]:
    conversations = await get_project_conversations(user.id, project_id)
    return conversations


@router.post("/chat-message-pydantic/{conversation_id}", response_model=ChatMessageInDB)
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


@router.post("/swe-result-approval-request", response_model=ImplementationApprovalResponse)
async def submit_swe_result_approval_request(
        implementation_summary: ImplementationSummary,
        user: Annotated[User, Depends(get_current_user)] = None) -> ImplementationApprovalResponse:

    if not await user_owns_conversation(user.id, implementation_summary.conversation_id):
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")

    messages = await get_chat_messages_pydantic(implementation_summary.conversation_id)

    approval_response = await orchestrator_agent.run(
        "The software engineer agent has submitted a solution.\n" +
        f"Its result is:\n\n{implementation_summary.model_dump_json()}\n\n " +
        "Decide whether to accept it, or reject it with feedback on what to fix before the solution is approved. " +
        "Just reject or approve the implementation with feedback. Do not worry about adding the entity to the project, it will be done automatically after approval.",
        output_type=ImplementationApprovalResponse,
        message_history=messages
    )

    return approval_response.output
