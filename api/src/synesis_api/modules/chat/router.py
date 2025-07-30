import uuid
import time
import json
import redis
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, RedirectResponse, Response
from typing import Annotated, List
from synesis_api.modules.chat.schema import (
    ChatMessage,
    ConversationWithMessages,
    UserChatMessageCreate,
    Context,
    ConversationCreate,
    ChatMessageInDB,
    Conversation
)
from synesis_api.modules.chat.service import (
    create_conversation,
    get_messages,
    get_messages_pydantic,
    create_message,
    create_messages_pydantic,
    get_conversations,
    get_conversation,
    create_context,
    get_context_message,
    get_current_conversation_mode,
    enter_conversation_mode,
)
from synesis_api.agents.chat.agent import chatbot_agent, OrchestratorOutput, JobStartOutput
from synesis_api.auth.service import get_current_user, user_owns_conversation, user_owns_job
from synesis_api.auth.schema import User
from synesis_api.modules.analysis.service import get_user_analyses_by_ids
from synesis_api.agents.analysis.agent import analysis_agent
from synesis_api.agents.analysis.runner import run_analysis_task
from synesis_api.modules.jobs.service import create_job, get_job
from synesis_api.agents.data_integration.data_integration_agent.runner import run_data_integration_task
from synesis_api.redis import get_redis
from synesis_api.secrets import SSE_MAX_TIMEOUT


router = APIRouter()


@router.post("/completions")
async def post_chat(
    prompt: UserChatMessageCreate,
    user: Annotated[User, Depends(get_current_user)] = None
) -> StreamingResponse:

    if not await user_owns_conversation(user.id, prompt.conversation_id):
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")

    context_in_db = None
    if prompt.context:
        context_in_db = await create_context(prompt.context)

    await create_message(
        prompt.conversation_id,
        "user",
        prompt.content,
        "chat",
        context_id=context_in_db.id if context_in_db else None,
        # Should probably define message_id here in the backend instead, but would need a more complex handshake implementation (which we can do later)
        id=prompt.message_id
    )

    conversation_mode = await get_current_conversation_mode(prompt.conversation_id)
    messages = await get_messages_pydantic(prompt.conversation_id)

    if conversation_mode.mode == "chat":
        orchestrator_run = await chatbot_agent.run(
            f"You need to decide which agent to handoff this prompt to: {prompt.content}. "
            "Choose between 'chat', 'analysis', 'data_integration' or 'automation'.",
            message_history=messages, output_type=OrchestratorOutput)

        handoff_agent = orchestrator_run.output.handoff_agent

        if handoff_agent == "analysis":

            raise HTTPException(
                status_code=501, detail="Analysis is not implemented yet")

        elif handoff_agent == "data_integration":

            job_id = uuid.uuid4()

            job_name = await chatbot_agent.run(
                f"Give me a nice human-readable name for a dataset with the following description: '{prompt.content}'. "
                "The name should be short and concise. Output just the name!"
            )

            job = await create_job(
                user.id,
                "data_integration",
                conversation_id=prompt.conversation_id,
                job_id=job_id,
                job_name=job_name.output
            )

            await run_data_integration_task.kiq(
                user_id=user.id,
                conversation_id=prompt.conversation_id,
                project_id=prompt.project_id,
                job_id=job.id,
                data_source_ids=prompt.context.data_source_ids,
                prompt_content=prompt.content
            )

            return RedirectResponse(url=f"/chat/response/{job_id}", status_code=303)

        elif handoff_agent == "chat":

            async def stream_chat_response():
                if conversation_mode.mode != "chat":
                    await enter_conversation_mode(prompt.conversation_id, "chat")

                message_id = uuid.uuid4()

                message = ChatMessageInDB(
                    id=message_id,
                    conversation_id=prompt.conversation_id,
                    role="agent",
                    content="",
                    type="chat",
                    job_id=None,
                    context_id=context_in_db.id if context_in_db else None,
                    created_at=datetime.now(timezone.utc)
                )

                async with chatbot_agent.run_stream(prompt.content, message_history=messages) as result:
                    prev_text = ""
                    async for text in result.stream(debounce_by=0.01):
                        if text != prev_text:
                            message.content = text
                            yield f"data: {message.model_dump_json()}\n\n"
                            prev_text = text

                new_messages = result.new_messages_json()

                await create_messages_pydantic(prompt.conversation_id, new_messages)
                await create_message(prompt.conversation_id, "agent", message.content, "chat", context_id=message.context_id, id=message.id)

            return StreamingResponse(stream_chat_response(), media_type="text/event-stream")

        else:
            raise HTTPException(
                status_code=501, detail="Internal agent error")

    else:
        raise HTTPException(
            status_code=501, detail="Interrupting agents is not implemented yet (this agent is not in chat mode). Please create a new chat conversation to run another agent.")


# Separate the completion route from the response route
# The response route is only needed for the completions that led to a job creation
# For simple chat responses we can just use the completion route
# The reasons for the separation is that we want to be able to exit the chat while having the job continue in the background
# We should then be able to hook back into the response endpoint at any time to get the current progress of the agent
@router.get("/response/{job_id}")
async def get_response(
    job_id: uuid.UUID,
    cache: Annotated[redis.Redis, Depends(get_redis)],
    user: Annotated[User, Depends(get_current_user)] = None,
) -> StreamingResponse:

    job = await get_job(job_id)

    if not user or not await user_owns_job(user.id, job_id):
        raise HTTPException(
            status_code=403, detail="You do not have permission to access this job")

    elif not job:
        raise HTTPException(
            status_code=404, detail="Job not found")

    elif job.status == "completed":
        return Response(content="Job is completed, see conversation for results.", media_type="text/plain")

    # Default timeout of 30 seconds
    timeout = 30
    timeout = min(timeout, SSE_MAX_TIMEOUT)

    async def stream_job_updates():
        response = await cache.xread({str(job_id): "$"}, count=1, block=timeout*1000)
        start_time = time.time()
        last_id = response[0][1][-1][0] if response else None

        while True:
            response = await cache.xread({str(job_id): last_id}, count=1)

            if response:
                start_time = time.time()
                last_id = response[0][1][-1][0]
                data = response[0][1][0][1]
                data_validated = ChatMessageInDB(**data)
                yield f"data: {data_validated.model_dump_json()}\n\n"

            if start_time + timeout < time.time():
                break

    return StreamingResponse(stream_job_updates(), media_type="text/event-stream")


@router.post("/conversation")
async def post_user_conversation(conversation_data: ConversationCreate, user: Annotated[User, Depends(get_current_user)] = None) -> Conversation:
    name = await chatbot_agent.run(f"""The user wants to start a new conversation. The user has written this: {conversation_data.content}. 
                                   What is the name of the conversation? Just give me the name of the conversation, no other text. 
                                   NB: Do not output a response to the prompt, that is done elsewhere! Just produce a suitable topic name given the prompt.
                                   """, output_type=str)
    name = name.output.replace('"', '').replace("'", "").strip()

    conversation_id = uuid.uuid4()

    conversation_in_db = await create_conversation(conversation_id, conversation_data.project_id, user.id, name)

    conversation = ConversationWithMessages(
        **conversation_in_db.model_dump(),
        messages=[],
        mode="chat"
    )

    return conversation


# Includes messages
@router.get("/conversation/{conversation_id}")
async def get_user_conversation(
        conversation_id: uuid.UUID,
        user: Annotated[User, Depends(get_current_user)] = None) -> ConversationWithMessages:
    if not await user_owns_conversation(user.id, conversation_id):
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")

    conversation = await get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=404, detail="Conversation not found")

    return conversation


# Excludes messages (to reduce overfetching)
@router.get("/conversations")
async def get_user_conversations(user: Annotated[User, Depends(get_current_user)] = None) -> List[Conversation]:
    conversations = await get_conversations(user.id)
    return conversations
