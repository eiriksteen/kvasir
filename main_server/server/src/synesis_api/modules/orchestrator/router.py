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
from synesis_api.utils.pydanticai_utils import helper_agent
from synesis_api.modules.project.service import get_projects
from synesis_api.modules.orchestrator.kvasir_v1.callbacks import ApplicationCallbacks
from kvasir_research.agents.kvasir_v1.agent import KvasirV1
from synesis_api.auth.service import get_current_user, user_owns_conversation
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
    project_objs = await get_projects(user.id, [prompt.project_id])
    if not project_objs:
        raise HTTPException(
            status_code=404, detail="Project not found")
    project_obj = project_objs[0]

    # context_message = await get_context_message(user.id, prompt.context)
    # project_graph_message = await get_project_description_message(user.id, conversation_record.project_id)
    # runs_status_message = await get_run_status_message(user.id, prompt.conversation_id)

    agent = KvasirV1(
        run_id=conversation_record.id,
        project_id=prompt.project_id,
        package_name=project_obj.python_package_name,
        sandbox_type="modal",
        callbacks=ApplicationCallbacks()
    )

    is_new_conversation = len(messages) == 0

    async def stream_response():
        response_message = ChatMessageInDB(
            id=uuid.uuid4(),
            conversation_id=conversation_record.id,
            role="assistant",
            type="chat",
            content="",
            context_id=None,
            created_at=datetime.now(timezone.utc)
        )

        prev_response_text = ""
        async for kvasir_v1_output, is_last in agent(prompt.content):
            if kvasir_v1_output != prev_response_text:
                response_message.content = kvasir_v1_output
                yield f"data: {response_message.model_dump_json(by_alias=True)}\n\n"
                await asyncio.sleep(SSE_MIN_SLEEP_TIME)
            if is_last:
                break

        if is_new_conversation:
            name = await helper_agent.run(
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
