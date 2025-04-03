import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Annotated, List
from pydantic_core import to_jsonable_python
from pydantic_ai.messages import ModelResponse, TextPart, ModelRequest, SystemPromptPart, ModelMessagesTypeAdapter
from ..ontology.service import get_user_datasets
from .schema import ChatMessage, Conversation, Prompt, Context
from .service import create_conversation, get_messages, get_messages_pydantic, insert_message, insert_message_pydantic, get_conversations
from .agent.agent import chatbot_agent
from ..auth.service import get_current_user, user_owns_conversation
from ..auth.schema import User


router = APIRouter()


@router.post("/completions/{conversation_id}")
async def post_chat(
    conversation_id: uuid.UUID,
    prompt: Prompt,
    user: Annotated[User, Depends(get_current_user)] = None
):

    if not await user_owns_conversation(user.id, conversation_id):
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")

    async def stream_messages():
        messages = await get_messages_pydantic(conversation_id)

        print(messages)

        async with chatbot_agent.run_stream(prompt.content, message_history=messages) as result:
            prev_text = ""
            async for text in result.stream(debounce_by=0.01):
                if text != prev_text:
                    yield text
                    prev_text = text

            print(result.new_messages())

            await insert_message_pydantic(conversation_id, result.new_messages_json())

        await insert_message(conversation_id, "user", prompt.content)
        await insert_message(conversation_id, "assistant", text)

    return StreamingResponse(stream_messages(), media_type="text/plain")


@router.post("/conversation")
async def post_conversation(user: Annotated[User, Depends(get_current_user)] = None) -> Conversation:
    conversation = await create_conversation(user.id)
    return conversation


@router.get("/conversation/{conversation_id}")
async def get_conversation(
        conversation_id: uuid.UUID,
        user: Annotated[User, Depends(get_current_user)] = None) -> List[ChatMessage]:

    if not await user_owns_conversation(user.id, conversation_id):
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")

    messages = await get_messages(conversation_id)

    return messages


@router.get("/conversations")
async def get_conversations(user: Annotated[User, Depends(get_current_user)] = None) -> List[Conversation]:
    conversations = await get_conversations(user.id)
    return conversations


@router.post("/context/{conversation_id}")
async def update_context(conversation_id: uuid.UUID, context: Context, user: Annotated[User, Depends(get_current_user)] = None):
    if not await user_owns_conversation(user.id, conversation_id):
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")

    datasets = await get_user_datasets(user.id, context.dataset_ids)
    automations = []

    updated_context = SystemPromptPart(
        content=f"""
        <CONTEXT UPDATES>
        Current datasets in context: {datasets}
        Current automations in context: {automations}
        </CONTEXT UPDATES>
        """
    )

    new_messages = [ModelRequest(parts=[updated_context])]
    messages_bytes = json.dumps(
        to_jsonable_python(new_messages)).encode("utf-8")
    await insert_message_pydantic(conversation_id, messages_bytes)

    return "Context updated"
