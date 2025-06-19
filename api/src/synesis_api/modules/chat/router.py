import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Annotated, List
from synesis_api.modules.chat.schema import ChatMessage, Conversation, Prompt, Context, ConversationCreate
from synesis_api.modules.chat.service import (
    create_conversation,
    get_messages,
    get_messages_pydantic,
    create_message,
    create_messages_pydantic,
    get_conversations,
    create_context,
    get_context_message,
)
from synesis_api.modules.chat.agent.agent import chatbot_agent, OrchestratorOutput
from synesis_api.auth.service import get_current_user, user_owns_conversation
from synesis_api.auth.schema import User
from synesis_api.modules.analysis.agent.agent import analysis_agent
from synesis_api.modules.analysis.agent.runner import analysis_agent_runner, AnalysisRequest, DelegateResult

router = APIRouter()


@router.post("/completions")
async def post_chat(
    prompt: Prompt,
    user: Annotated[User, Depends(get_current_user)] = None
):

    if not await user_owns_conversation(user.id, prompt.conversation_id):
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")
    

    if prompt.context:
        context_in_db = await create_context(prompt.context)

    await create_message(prompt.conversation_id, "user", prompt.content, context_in_db.id if context_in_db else None)
    
    async def stream_messages():
        messages = await get_messages_pydantic(prompt.conversation_id)
        orchestrator_output = await chatbot_agent.run("You need to decide which agent to handoff this prompt to: " + prompt.content + ". Choose between 'chat', 'analysis', or 'automation'.", message_history=messages, output_type=OrchestratorOutput)
        handoff_agent = orchestrator_output.output.handoff_agent
        context_message = await get_context_message(user.id, prompt.context)

        if handoff_agent == "chat":
            async with chatbot_agent.run_stream(prompt.content, message_history=messages) as result:
                prev_text = ""
                async for text in result.stream(debounce_by=0.01):
                    if text != prev_text:
                        yield text
                        prev_text = text

            new_messages = result.new_messages_json()

            await create_messages_pydantic(prompt.conversation_id, new_messages)
            
            await create_message(prompt.conversation_id, "assistant", text)

        elif handoff_agent == "analysis" or handoff_agent == "automation":
            delegation_prompt = f"This is the current context: {context_message}. This is the user prompt: {prompt.content}. You can delegate the task to one of the following functions: " + ", ".join([f"'{func}'" for func in ["run_analysis_planner", "run_execution_agent", "run_simple_analysis"]]) + ". Which function do you want to delegate the task to?"
            delegated_task = await analysis_agent.run(delegation_prompt, output_type=DelegateResult)
            delegated_task = delegated_task.output.function_name

            analysis_request = AnalysisRequest(
                project_id=prompt.context.project_id,
                dataset_ids=prompt.context.dataset_ids,
                automation_ids=prompt.context.automation_ids,
                analysis_ids=prompt.context.analysis_ids,
                prompt=prompt.content,
                user=user,
                message_history=messages,
                conversation_id=prompt.conversation_id,
            )

            async for item in analysis_agent_runner(analysis_request, delegated_task):
                yield item


        else:
            raise HTTPException(
                status_code=400, detail="Invalid handoff agent")
        
        
        

    return StreamingResponse(stream_messages(), media_type="text/plain")


@router.post("/conversation")
async def post_user_conversation(conversation_data: ConversationCreate, user: Annotated[User, Depends(get_current_user)] = None) -> Conversation:
    name = await chatbot_agent.run(f"""The user wants to start a new conversation. The user has written this: {conversation_data.content}. 
                                   What is the name of the conversation? Just give me the name of the conversation, no other text.
                                   """, output_type=str)
    name = name.output.replace('"', '').replace("'", "").strip()

    conversation_id = uuid.uuid4()

    conversation_in_db = await create_conversation(conversation_id, conversation_data.project_id, user.id, name)

    conversation = Conversation(
        **conversation_in_db.model_dump(),
        messages=[]
    )
    
    return conversation


@router.get("/conversation/{conversation_id}")
async def get_user_conversation(
        conversation_id: uuid.UUID,
        user: Annotated[User, Depends(get_current_user)] = None) -> List[ChatMessage]:
    if not await user_owns_conversation(user.id, conversation_id):
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")

    messages = await get_messages(conversation_id)
    return messages


@router.get("/conversations")
async def get_user_conversations(user: Annotated[User, Depends(get_current_user)] = None) -> List[Conversation]:
    conversations = await get_conversations(user.id)
    return conversations


@router.get("/context/{conversation_id}")
async def get_context(conversation_id: uuid.UUID, user: Annotated[User, Depends(get_current_user)] = None) -> Context:
    if not await user_owns_conversation(user.id, conversation_id):
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")

    context = await get_context(conversation_id, user.id)
    return context
