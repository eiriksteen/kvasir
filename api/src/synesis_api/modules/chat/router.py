import json
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Annotated, List, Literal
from pydantic_core import to_jsonable_python
from pydantic_ai.messages import ModelRequest, SystemPromptPart
from synesis_api.modules.ontology.service import get_user_datasets_by_ids
from synesis_api.modules.chat.schema import ChatMessage, Conversation, Prompt, Context, ContextCreate
from synesis_api.modules.chat.service import (
    create_conversation,
    get_messages,
    get_messages_pydantic,
    create_message,
    create_messages_pydantic,
    get_conversations,
    create_context,
    get_context_by_time_stamp
)
from synesis_api.modules.chat.agent.agent import chatbot_agent
from synesis_api.auth.service import get_current_user, user_owns_conversation
from synesis_api.auth.schema import User
from synesis_api.modules.ontology.schema import Dataset
from synesis_api.modules.analysis.service import get_user_analyses_by_ids
from synesis_api.modules.orchestrator.agent.agent import orchestrator_agent
from synesis_api.modules.analysis.schema import AnalysisRequest
from synesis_api.modules.analysis.agent.agent import analysis_agent
from synesis_api.modules.analysis.tasks import run_analysis_planner_task, run_analysis_execution_task
router = APIRouter()

@router.post("/completions/analysis-planner/{conversation_id}")
async def post_chat(
    conversation_id: uuid.UUID,
    prompt: Prompt,
    datasets: List[Dataset],
    # automations: List[Automation],
    user: Annotated[User, Depends(get_current_user)] = None
):
    if not await user_owns_conversation(user.id, conversation_id):
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")
    
    # TODO: should all things that go through chat be handled here?


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
        orchestrator_output = await orchestrator_agent.run(prompt.content, message_history=messages)
        handoff_agent = orchestrator_output.output.handoff_agent
    
        if handoff_agent == "chat":
            async with chatbot_agent.run_stream(prompt.content, message_history=messages) as result:
                prev_text = ""
                async for text in result.stream(debounce_by=0.01):
                    if text != prev_text:
                        yield text
                        prev_text = text
        elif handoff_agent == "analysis" or handoff_agent == "automation":
            context = await get_context_by_time_stamp(conversation_id, user.id, datetime.now())
            delegated_task = await analysis_agent.delegate("This is the current context: " + context.model_dump_json() + "Which function to delegate this prompt to: " + prompt.content)

            analysis_request = AnalysisRequest(
                dataset_ids=context.dataset_ids,
                automation_ids=context.automation_ids,
                analysis_ids=context.analysis_ids,
                prompt=prompt.content,
                user=user,
                message_history=messages
            )

            if delegated_task == "run_simple_analysis": 
                async for item in analysis_agent.run_simple_analysis(analysis_request):
                    if isinstance(item, str):
                        yield item
                    elif isinstance(item, AgentRunResult):
                        new_messages = messages + item.all_messages()
                        async with chatbot_agent.run_stream(prompt.content, message_history=new_messages) as result:
                            prev_text = ""
                            async for text in result.stream(debounce_by=0.01):
                                if text != prev_text:
                                    yield text
                                    prev_text = text
            elif delegated_task == "run_analysis_planner":
                yield "Running analysis planner. This may take a couple of minutes. The results will be shown in the analyis tab."
                await run_analysis_planner_task.kiq(analysis_request)
            elif delegated_task == "run_execution_agent":
                yield "Running analysis execution. This may take a couple of minutes. The results will be shown in the analyis tab."
                await run_analysis_execution_task.kiq(analysis_request)
            else:
                raise HTTPException(
                    status_code=400, detail="Invalid handoff agent")
            

        await insert_message_pydantic(conversation_id, result.new_messages_json())

        await create_message(conversation_id, "user", prompt.content)
        await create_message(conversation_id, "assistant", text)

    return StreamingResponse(stream_messages(), media_type="text/plain")


@router.post("/conversation")
async def post_user_conversation(user: Annotated[User, Depends(get_current_user)] = None) -> Conversation:
    conversation = await create_conversation(user.id)
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

    context = await get_context_by_time_stamp(conversation_id, user.id, datetime.now())
    return context


@router.post("/context")
async def update_context(
        context: ContextCreate,
        user: Annotated[User, Depends(get_current_user)] = None) -> ContextCreate:



    if not await user_owns_conversation(user.id, context.conversation_id):
        raise HTTPException(
            status_code=403, detail="You do not have access to this conversation")

    current_context = await get_context_by_time_stamp(context.conversation_id, user.id, datetime.now())
    
    if context.remove:
        # When removing, we need to get the current context and remove the specified IDs
        if current_context is None:
            return context  # Nothing to remove if no current context
            
        # Start with all current IDs
        new_dataset_ids = [id for id in current_context.dataset_ids]
        new_analysis_ids = [id for id in current_context.analysis_ids]
        
        # Remove the specified IDs
        new_dataset_ids = [id for id in new_dataset_ids if id not in context.dataset_ids]
        new_analysis_ids = [id for id in new_analysis_ids if id not in context.analysis_ids]
    elif context.append:
        # When appending, combine new IDs with existing ones
        new_dataset_ids = [id for id in context.dataset_ids]
        new_analysis_ids = [id for id in context.analysis_ids]
        if current_context is not None:
            new_dataset_ids += [id for id in current_context.dataset_ids]
            new_analysis_ids += [id for id in current_context.analysis_ids]
    else:
        # When not appending and not removing, use only the new IDs
        new_dataset_ids = [id for id in context.dataset_ids]
        new_analysis_ids = [id for id in context.analysis_ids]

    # Remove duplicates while preserving order
    new_dataset_ids = list(dict.fromkeys(new_dataset_ids))
    new_analysis_ids = list(dict.fromkeys(new_analysis_ids))

    datasets = await get_user_datasets_by_ids(user.id, new_dataset_ids)
    automations = []
    analyses = await get_user_analyses_by_ids(user.id, new_analysis_ids)

    updated_context = SystemPromptPart( # TODO: this is a very bad way of doing this, this should only be called when the user actually prompts the agent, or else the context will be very cluttered.
        content=f"""
        <CONTEXT UPDATES>
        Current datasets in context: {datasets}
        Current automations in context: {automations}
        Current analyses in context: {analyses}
        </CONTEXT UPDATES>
        """
    )

    new_messages = [ModelRequest(parts=[updated_context])]
    messages_bytes = json.dumps(
        to_jsonable_python(new_messages)).encode("utf-8")

    await insert_context(user.id, context.conversation_id, new_dataset_ids, context.automation_ids, new_analysis_ids)
    await insert_message_pydantic(context.conversation_id, messages_bytes)

    return context
