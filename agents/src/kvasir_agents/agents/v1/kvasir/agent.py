from uuid import UUID, uuid4
from taskiq import Context as TaskiqContext, TaskiqDepends
from typing import List, Tuple, Annotated, AsyncGenerator, Dict, Optional
from pydantic_ai import Agent, RunContext, ModelSettings, PromptedOutput

from kvasir_agents.agents.v1.broker import v1_broker
from kvasir_agents.agents.v1.callbacks import KvasirV1Callbacks
from kvasir_agents.agents.v1.kvasir.knowledge_bank import SUPPORTED_TASKS_LITERAL
from kvasir_agents.agents.v1.analysis.agent import AnalysisAgentV1
from kvasir_agents.agents.v1.swe.agent import SweAgentV1
from kvasir_agents.agents.v1.swe.deps import SWEDeps
from kvasir_agents.agents.v1.kvasir.deps import KvasirV1Deps
from kvasir_agents.agents.v1.base_agent import AgentV1, Context
from kvasir_agents.agents.v1.data_model import RunCreate, MessageCreate, Message
from kvasir_agents.agents.v1.shared_tools import navigation_toolset, knowledge_bank_toolset
from kvasir_agents.agents.v1.kvasir.prompt import KVASIR_V1_SYSTEM_PROMPT
from kvasir_agents.agents.v1.analysis.deps import AnalysisDeps
from kvasir_agents.agents.v1.kvasir.tools import dispatch_agents, DispatchAgentsOutput, read_entities, explain_action_plan
from kvasir_agents.utils.agent_utils import get_model
from kvasir_agents.agents.v1.history_processors import (
    keep_only_most_recent_project_description,
    keep_only_most_recent_folder_structure,
    keep_only_most_recent_entity_context
)


@v1_broker.task
async def start_swe_run_from_orchestrator(
    prompt: str,
    # Cant pass deps direct since taskiq can't serialize
    deps_dict: Dict,
    bearer_token: str,
    taskiq_context: Annotated[TaskiqContext, TaskiqDepends()],
    context: Optional[Context] = None
) -> str:

    callbacks: KvasirV1Callbacks = taskiq_context.state.callbacks
    swe_deps = SWEDeps(
        **deps_dict,
        callbacks=callbacks,
        bearer_token=bearer_token
    )
    swe_agent = SweAgentV1(swe_deps)
    swe_run_result = await swe_agent(prompt, context=context)
    pipeline_desc = await swe_deps.ontology.describe_entity(swe_deps.pipeline_id, "pipeline", include_connections=False)

    if not await callbacks.get_run_status(swe_deps.user_id, swe_deps.kvasir_run_id) == "running":
        kvasir_v1 = await KvasirV1.from_run(swe_deps.user_id, swe_deps.kvasir_run_id, callbacks)
        await kvasir_v1(f"SWE run {swe_deps.run_id} completed. The result pipeline is:\n\n{pipeline_desc}")

    return swe_run_result


@v1_broker.task
async def resume_swe_run_from_orchestrator(
    user_id: UUID,
    swe_run_id: UUID,
    kvasir_run_id: UUID,
    message: str,
    time_limit: int,
    guidelines: List[SUPPORTED_TASKS_LITERAL],
    bearer_token: str,
    taskiq_context: Annotated[TaskiqContext, TaskiqDepends()],
    context: Optional[Context] = None,
) -> str:

    callbacks: KvasirV1Callbacks = taskiq_context.state.callbacks
    swe_agent = await SweAgentV1.from_run(user_id, swe_run_id, callbacks, bearer_token=bearer_token)
    swe_agent.update_time_limit(time_limit)
    swe_agent.update_guidelines(guidelines)
    swe_run_result = await swe_agent(message, context=context)
    pipeline_desc = await swe_agent.deps.ontology.describe_entity(swe_agent.deps.pipeline_id, "pipeline", include_connections=False)

    if not await callbacks.get_run_status(user_id, kvasir_run_id) == "running":
        kvasir_v1 = await KvasirV1.from_run(user_id, kvasir_run_id, callbacks)
        await kvasir_v1(f"SWE run {swe_run_id} completed. The updated pipeline is:\n\n{pipeline_desc}")

    return swe_run_result


@v1_broker.task
async def start_analysis_run_from_orchestrator(
    prompt: str,
    kvasir_run_id: UUID,
    deps_dict: Dict,
    bearer_token: str,
    taskiq_context: Annotated[TaskiqContext, TaskiqDepends()],
    context: Optional[Context] = None,
) -> str:

    callbacks: KvasirV1Callbacks = taskiq_context.state.callbacks
    analysis_deps = AnalysisDeps(
        **deps_dict, callbacks=callbacks, bearer_token=bearer_token)
    analysis_agent = AnalysisAgentV1(deps=analysis_deps)
    analysis_run_result = await analysis_agent(prompt, context=context)
    analysis_desc = await analysis_deps.ontology.describe_entity(analysis_deps.analysis_id, "analysis", include_connections=False)

    if not await callbacks.get_run_status(analysis_deps.user_id, kvasir_run_id) == "running":
        kvasir_v1 = await KvasirV1.from_run(analysis_deps.user_id, kvasir_run_id, callbacks)
        await kvasir_v1(f"Analysis run {analysis_deps.run_id} completed. The result analysis is:\n\n{analysis_desc}")

    return analysis_run_result


@v1_broker.task
async def resume_analysis_run_from_orchestrator(
    user_id: UUID,
    analysis_run_id: UUID,
    kvasir_run_id: UUID,
    message: str,
    time_limit: int,
    guidelines: List[SUPPORTED_TASKS_LITERAL],
    bearer_token: str,
    taskiq_context: Annotated[TaskiqContext, TaskiqDepends()],
    context: Optional[Context] = None,
) -> str:

    callbacks: KvasirV1Callbacks = taskiq_context.state.callbacks
    analysis_agent = await AnalysisAgentV1.from_run(user_id, analysis_run_id, callbacks, bearer_token=bearer_token)
    analysis_agent.update_time_limit(time_limit)
    analysis_agent.update_guidelines(guidelines)
    analysis_run_result = await analysis_agent(message, context=context)
    analysis_desc = await analysis_agent.deps.ontology.describe_entity(analysis_agent.deps.analysis_id, "analysis", include_connections=False)

    if not await callbacks.get_run_status(user_id, kvasir_run_id) == "running":
        kvasir_v1 = await KvasirV1.from_run(user_id, kvasir_run_id, callbacks)
        await kvasir_v1(f"Analysis run {analysis_agent.deps.run_id} completed. The result analysis is:\n\n{analysis_desc}")

    return analysis_run_result


# Wrapper to launch the agents. We need it here since we relaunch Kvasir when the agents are done, and otherwise would be circular imports
async def dispatch_agents_from_orchestrator(
        ctx: RunContext[KvasirV1Deps],
    output: DispatchAgentsOutput,
) -> DispatchAgentsOutput:
    out = await dispatch_agents(ctx, output)

    await ctx.deps.callbacks.log(
        ctx.deps.user_id, ctx.deps.run_id, f"Agent dispatch output:\n\n{out.model_dump_json(indent=2)}", "info")

    # Launch analysis runs
    for analysis_run_to_launch in out.analysis_runs_to_launch:
        analysis_deps = AnalysisDeps(
            user_id=ctx.deps.user_id,
            project_id=ctx.deps.project_id,
            package_name=ctx.deps.package_name,
            callbacks=ctx.deps.callbacks,
            sandbox_type=ctx.deps.sandbox_type,
            bearer_token=ctx.deps.bearer_token,
            kvasir_run_id=ctx.deps.run_id,
            data_paths=analysis_run_to_launch.data_paths,
            time_limit=analysis_run_to_launch.time_limit,
            guidelines=analysis_run_to_launch.guidelines,
            run_name=analysis_run_to_launch.run_name,
            run_id=None,
            analysis_id=analysis_run_to_launch.analysis_id,
        )
        await start_analysis_run_from_orchestrator.kiq(
            prompt=analysis_run_to_launch.deliverable_description,
            kvasir_run_id=ctx.deps.run_id,
            deps_dict=analysis_deps.to_dict(),
            bearer_token=ctx.deps.bearer_token,
            context=analysis_run_to_launch.entities_to_inject,
        )

    # Resume analysis runs
    for analysis_run_to_resume in out.analysis_runs_to_resume:
        await resume_analysis_run_from_orchestrator.kiq(
            user_id=ctx.deps.user_id,
            analysis_run_id=analysis_run_to_resume.run_id,
            kvasir_run_id=ctx.deps.run_id,
            message=analysis_run_to_resume.message,
            time_limit=analysis_run_to_resume.time_limit,
            guidelines=analysis_run_to_resume.guidelines if analysis_run_to_resume.guidelines else [],
            bearer_token=ctx.deps.bearer_token,
            context=analysis_run_to_resume.entities_to_inject,
        )

    # Launch SWE runs
    for swe_run_to_launch in out.swe_runs_to_launch:
        swe_deps = SWEDeps(
            user_id=ctx.deps.user_id,
            project_id=ctx.deps.project_id,
            package_name=ctx.deps.package_name,
            callbacks=ctx.deps.callbacks,
            sandbox_type=ctx.deps.sandbox_type,
            bearer_token=ctx.deps.bearer_token,
            kvasir_run_id=ctx.deps.run_id,
            data_paths=swe_run_to_launch.data_paths,
            read_only_paths=swe_run_to_launch.read_only_paths,
            time_limit=swe_run_to_launch.time_limit,
            guidelines=swe_run_to_launch.guidelines,
            modified_files={},
            run_name=swe_run_to_launch.run_name,
            run_id=None,
        )
        await start_swe_run_from_orchestrator.kiq(
            prompt=swe_run_to_launch.deliverable_description,
            deps_dict=swe_deps.to_dict(),
            bearer_token=ctx.deps.bearer_token,
            context=swe_run_to_launch.entities_to_inject,
        )

    # Resume SWE runs
    for swe_run_to_resume in out.swe_runs_to_resume:
        await resume_swe_run_from_orchestrator.kiq(
            user_id=ctx.deps.user_id,
            swe_run_id=swe_run_to_resume.run_id,
            kvasir_run_id=ctx.deps.run_id,
            message=swe_run_to_resume.message,
            time_limit=swe_run_to_resume.time_limit,
            guidelines=swe_run_to_resume.guidelines if swe_run_to_resume.guidelines else [],
            bearer_token=ctx.deps.bearer_token,
            context=swe_run_to_resume.entities_to_inject
        )

    return out


model = get_model()


kvasir_v1_agent = Agent[KvasirV1Deps, str](
    model,
    deps_type=KvasirV1Deps,
    toolsets=[navigation_toolset, knowledge_bank_toolset],
    tools=[
        explain_action_plan,
        dispatch_agents_from_orchestrator,
        read_entities
    ],
    output_type=PromptedOutput(str),
    retries=3,
    model_settings=ModelSettings(temperature=0),
    history_processors=[
        keep_only_most_recent_project_description,
        keep_only_most_recent_folder_structure,
        keep_only_most_recent_entity_context
    ]
)


@kvasir_v1_agent.system_prompt
async def kvasir_v1_system_prompt(ctx: RunContext[KvasirV1Deps]) -> str:
    current_wd = await ctx.deps.sandbox.get_working_directory()
    env_description = ctx.deps.sandbox.get_pyproject_for_env_description()

    full_system_prompt = (
        f"{KVASIR_V1_SYSTEM_PROMPT}\n\n" +
        f"Current working directory: {current_wd}\n\n" +
        f"You environment is described by the following pyproject.toml:\n\n<pyproject>\n{env_description}\n</pyproject>\n\n"
    )

    return full_system_prompt


class KvasirV1(AgentV1[KvasirV1Deps, str]):
    deps_class = KvasirV1Deps
    deps: KvasirV1Deps

    def __init__(self, deps: KvasirV1Deps):
        super().__init__(deps, kvasir_v1_agent)

    async def _setup_run(self) -> UUID:
        if self.deps.run_id is None:
            run = await self.deps.callbacks.create_run(
                self.deps.user_id,
                RunCreate(type="kvasir", project_id=self.deps.project_id, run_name=self.deps.run_name or "Kvasir Run", initial_status="running"))
            self.deps.run_id = run.id

        await self.deps.callbacks.set_run_status(self.deps.user_id, self.deps.run_id, "running")
        return self.deps.run_id

    async def run_agent_text_stream(self, prompt: str, context: Optional[Context] = None) -> AsyncGenerator[Message, None]:

        await self.deps.callbacks.create_message(
            self.deps.user_id,
            MessageCreate(
                run_id=self.deps.run_id,
                content=prompt,
                role="user",
                type="chat"
            )
        )

        output_id = uuid4()
        async for response in super().run_agent_text_stream(prompt, context, describe_folder_structure=True):
            yield Message(
                id=output_id,
                run_id=self.deps.run_id,
                content=response,
                role="kvasir",
                type="chat"
            )

        await self.deps.callbacks.create_message(self.deps.user_id, MessageCreate(
            run_id=self.deps.run_id,
            content=response,
            role="kvasir",
            type="chat"
        ))

    async def __call__(self, prompt: str, context: Optional[Context] = None) -> str:
        async for response in self.run_agent_text_stream(prompt, context):
            pass
        return response

    async def run_agent_streaming(self, prompt: str, context: Optional[Context] = None) -> AsyncGenerator[Tuple[Message, bool], None]:
        async for response in self.run_agent_text_stream(prompt, context):
            yield response, False
        yield response, True
