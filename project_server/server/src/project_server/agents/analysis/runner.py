import uuid
import asyncio
from typing import Tuple, List, Literal, Optional
from pydantic_ai import Agent
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import SystemPromptPart, ModelRequest
from project_server.agents.analysis.prompt import ANALYSIS_AGENT_SYSEM_PROMPT
from project_server.agents.analysis.agent import analysis_agent, AnalysisDeps
from project_server.worker import logger, broker
from pydantic_ai.messages import (
    ModelMessage,
    FunctionToolCallEvent,
)
# from project_server.modules.runs.service import update_run_status
# from project_server.client import (
#     create_chat_message_pydantic, 
#     create_chat_message,
#     update_run_status
# )
from pydantic import BaseModel
from project_server.agents.runner_base import RunnerBase
from synesis_schemas.project_server import RunAnalysisRequest
from project_server.client import ProjectClient, post_run_message, post_run, patch_run_status
from project_server.redis import get_redis
from synesis_schemas.main_server import RunMessageCreate, RunCreate, RunStatusUpdate
from datetime import datetime, timezone



class AnalysisReportResult(BaseModel):
    analysis_report: str
    analysis_code: str



class AnalysisAgentRunner:
    def __init__(
        self,
        bearer_token: str,
    ):
        self.agent = analysis_agent
        self.logger = logger
        
        self.bearer_token = bearer_token
        self.project_client = ProjectClient()
        self.project_client.set_bearer_token(bearer_token)
        self.redis_stream = get_redis()

    # TODO: copied from runner_base.py, should inherit from it.
    async def _log_message_to_redis(
            self,
            content: str,
            message_type: Literal["tool_call", "result", "error"],
            write_to_db: bool = True
    ):
        """Log a message to Redis stream"""

        message = {
            "id": str(uuid.uuid4()),
            "role": "agent",
            "content": content,
            "run_id": str(self.run_id),
            "type": message_type,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.redis_stream.xadd(str(self.run_id), message)

        if write_to_db:
            await post_run_message(self.project_client, RunMessageCreate(
                type=message_type,
                run_id=str(self.run_id),
                content=content
            ))

    async def simulate_streaming(self, text: str):
        tot_text = ""
        num_chunks = len(text) // 3
        rest = len(text) % 3

        for i in range(0, num_chunks):
            tot_text += text[i*3:(i+1)*3]
            yield tot_text
            await asyncio.sleep(0.01)

        if rest > 0:
            tot_text += text[num_chunks*3:num_chunks*3+rest]
            yield tot_text
            await asyncio.sleep(0.01)
        
    
    def _yielder(self, tool_name: str) -> Tuple[Literal["tool_call"], str]:
        if tool_name == "get_column_names":
            return "Reading structure of dataset..."
        elif tool_name == "get_data_path":
            return "Reading data from dataset..."
        elif tool_name == "search_through_datasets":
            return "Searching through datasets..."
        elif tool_name == "edit_analysis_result":
            return "Editing analysis result..."
        elif tool_name == "add_analysis_result_to_notebook_section":
            return "Adding analysis result to section..."
        elif tool_name == "create_notebook_section":
            return "Creating notebook section..."
        elif tool_name == "search_knowledge_bank":
            return "Searching knowledge bank..."
        elif tool_name == "generate_analysis_result":
            return "Generating and running code..."
        elif tool_name == "move_analysis_result_to_section":
            return "Moving analysis result to section..."
        elif tool_name == "delete_notebook_section":
            return "Deleting notebook section..."
        elif tool_name == "create_empty_analysis_result":
            return "Setting up analysis..."
        elif tool_name == "search_through_analysis_objects":
            return "Searching through analysis objects..."
        elif tool_name == "edit_section_name":
            return "Editing section name..."
        elif tool_name == "move_sections":
            return "Moving section..."
        elif tool_name == "plot_analysis_result":
            return "Plotting analysis result..."
        elif tool_name == "search_through_analysis_results":
            return "Searching through analysis results..."
        elif tool_name == "create_table_for_analysis_result":
            return "Creating table for analysis result..."
        else:
            return f"Calling cached tool for analysis... {tool_name}"
        
    async def _prepare_agent_run(self, analysis_request: RunAnalysisRequest) -> Tuple[AnalysisDeps, List[ModelMessage]]:
        system_prompt = SystemPromptPart(
            content= f"""
                {ANALYSIS_AGENT_SYSEM_PROMPT}
                The user has provided the following context: {analysis_request.context_message}
            """
        )
        run_in_db = await post_run(self.project_client, RunCreate(
                conversation_id=analysis_request.conversation_id,
                user_id=analysis_request.user_id,
                type="analysis",
            ))

        self.run_id = run_in_db.id

        model_request = ModelRequest(parts=[system_prompt])
        message_history = analysis_request.message_history + [model_request]


        analysis_deps = AnalysisDeps(
            analysis_request=analysis_request,
            client=self.project_client,
            run_id=run_in_db.id
        )

        return analysis_deps, message_history
        
    async def __call__(
            self,
            analysis_request: RunAnalysisRequest,
    ):
        try:
            analysis_deps, message_history = await self._prepare_agent_run(analysis_request)

            async with self.agent.iter(
                f"""Solve this user prompt: {analysis_request.prompt}. 
                """,
                output_type=str,
                message_history=message_history,
                deps=analysis_deps
            ) as run:
                async for node in run:
                    if Agent.is_call_tools_node(node):
                        async with node.stream(run.ctx) as handle_stream:
                            async for event in handle_stream:
                                if isinstance(event, FunctionToolCallEvent):
                                    tool_content = self._yielder(event.part.tool_name)
                                    logger.info("tool_content: " + tool_content)
                                    await self._log_message_to_redis(tool_content, "tool_call")

            pydantic_messages_to_db = run.result.new_messages_json()
        #     await create_chat_message_pydantic(analysis_request.conversation_id, [pydantic_messages_to_db])
        #     await create_chat_message(analysis_request.conversation_id, "assistant", run.result.output)
        #     # TODO: figure out a way to stream to chat through redis
        #     # async for sub_text in self.simulate_streaming(run.result.output):
        #     #     await self._log_message_to_redis(sub_text, 'result', False) # set to false to avoid writing multiple messages to db
        #     # await self._log_message_to_redis(sub_text, 'result', True)
            await patch_run_status(self.project_client, RunStatusUpdate(
                    run_id=self.run_id,
                    status="completed"
                ))
        except Exception as e:
            await patch_run_status(self.project_client, RunStatusUpdate(
                run_id=self.run_id,
                status="failed"
            ))
            raise e
    

@broker.task
async def run_analysis_task(
    analysis_request: RunAnalysisRequest,
    bearer_token: str
):
    runner = AnalysisAgentRunner(
        bearer_token
    )

    await runner(analysis_request)