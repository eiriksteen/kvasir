import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Annotated, List
from synesis_api.modules.orchestrator.schema import (
    ConversationWithMessages,
    UserChatMessageCreate,
    ConversationCreate,
    ChatMessageInDB,
    Conversation,
)
from synesis_api.modules.orchestrator.service import (
    create_conversation,
    get_chat_messages_pydantic,
    create_chat_message,
    get_conversations,
    get_conversation_with_jobs_and_messages,
    create_context,
    create_chat_message_pydantic,
    get_context_message,
)
from synesis_api.agents.chat.agent import chatbot_agent, OrchestratorOutput
from synesis_api.auth.service import get_current_user, user_owns_conversation
from synesis_api.auth.schema import User
from synesis_api.agents.data_integration.data_integration_agent.runner import run_data_integration_task
from synesis_api.modules.runs.service import create_run


router = APIRouter()


# This endpoint may launch agent runs
# The frontend should listen to the runs sse endpoint to listen for when this happens
# Then, the messages/{run_id} can be used to listen to the messages
@router.post("/completions")
async def post_chat(
    prompt: UserChatMessageCreate,
    user: Annotated[User, Depends(get_current_user)] = None
) -> StreamingResponse:

    if not await user_owns_conversation(user.id, prompt.conversation_id):
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")

    messages = await get_chat_messages_pydantic(prompt.conversation_id)

    # TODO: Important to optimize this, as it will blow up the context with repeated messages!
    # One option is to keep the full entity objects just for the current context, and collapse to the IDs and names for the past ones
    context_message = await get_context_message(user.id, prompt.context)

    orchestrator_run = await chatbot_agent.run(
        f"The user prompt is: '{prompt.content}'. "
        "Decide whether to launch an agent or just respond directly to the prompt. "
        "If launching an agent, choose between 'analysis', 'data_integration' or 'automation'. If not just choose 'chat'. "
        f"The context is:\n {context_message}",
        message_history=messages, output_type=OrchestratorOutput)

    handoff_agent = orchestrator_run.output.handoff_agent

    async def stream_response():

        response_message = ChatMessageInDB(
            id=uuid.uuid4(),
            conversation_id=prompt.conversation_id,
            role="agent",
            content="",
            context_id=None,
            created_at=datetime.now(timezone.utc)
        )

        context_in_db = None
        if prompt.context:
            context_in_db = await create_context(prompt.context)
            response_message.context_id = context_in_db.id

        async with chatbot_agent.run_stream(
            "Now respond to the user! If you launched an agent, explain what you did. If not, just respond directly to the user prompt.",
            message_history=messages+orchestrator_run.new_messages()
        ) as result:
            prev_text = ""
            async for text in result.stream(debounce_by=0.01):
                if text != prev_text:
                    response_message.content = text
                    yield f"data: {response_message.model_dump_json()}\n\n"
                    prev_text = text

        await create_chat_message(
            prompt.conversation_id,
            "user",
            prompt.content,
            context_id=context_in_db.id if context_in_db else None,
            # Should probably define message_id here in the backend instead, but would need a more complex handshake implementation (which we can do later)
            id=prompt.message_id
        )
        await create_chat_message(prompt.conversation_id, "assistant", response_message.content, response_message.context_id, response_message.id)
        await create_chat_message_pydantic(prompt.conversation_id, orchestrator_run.new_messages_json() + result.new_messages_json())

        if handoff_agent == "analysis":
            raise HTTPException(
                status_code=501, detail="Analysis is not implemented yet")

        elif handoff_agent == "data_integration":

            run = await create_run(
                prompt.conversation_id,
                user.id,
                "data_integration",
                context_id=context_in_db.id if context_in_db else None,
                run_name=orchestrator_run.output.run_name
            )

            await run_data_integration_task.kiq(
                user_id=user.id,
                conversation_id=prompt.conversation_id,
                project_id=prompt.project_id,
                run_id=run.id,
                data_source_ids=prompt.context.data_source_ids,
                prompt_content=prompt.content
            )

    return StreamingResponse(stream_response(), media_type="text/event-stream")


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

    conversation = await get_conversation_with_jobs_and_messages(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=404, detail="Conversation not found")

    return conversation


# Excludes messages (to reduce overfetching)
@router.get("/conversations")
async def get_user_conversations(user: Annotated[User, Depends(get_current_user)] = None) -> List[Conversation]:
    conversations = await get_conversations(user.id)
    return conversations
