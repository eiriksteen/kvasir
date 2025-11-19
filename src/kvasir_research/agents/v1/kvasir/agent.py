from uuid import UUID
from dataclasses import fields
from collections import OrderedDict
from taskiq import Context, TaskiqDepends
from typing import List, Tuple, Annotated, AsyncGenerator, Dict
from pydantic_ai import Agent, RunContext, ModelSettings

from kvasir_research.agents.v1.broker import v1_broker
from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks
from kvasir_research.agents.v1.kvasir.knowledge_bank import SUPPORTED_TASKS_LITERAL
from kvasir_research.agents.v1.analysis.agent import AnalysisAgentV1
from kvasir_research.agents.v1.swe.agent import SweAgentV1
from kvasir_research.agents.v1.swe.deps import SWEDeps
from kvasir_research.agents.v1.kvasir.deps import KvasirV1Deps
from kvasir_research.agents.v1.kvasir.output import KvasirOutput, submit_kvasir_response
from kvasir_research.agents.v1.base_agent import AgentV1
from kvasir_research.agents.v1.data_model import RunBase, RunCreate
from kvasir_research.agents.v1.shared_tools import navigation_toolset, knowledge_bank_toolset
from kvasir_research.agents.v1.kvasir.prompt import KVASIR_V1_SYSTEM_PROMPT
from kvasir_research.agents.v1.analysis.deps import AnalysisDeps
from kvasir_research.utils.agent_utils import get_model


@v1_broker.task
async def start_swe_run_from_orchestrator(
        prompt: str,
        kvasir_run_id: UUID,
        swe_deps_serializable_dict: Dict,
        context: Annotated[Context, TaskiqDepends()]) -> str:

    callbacks: KvasirV1Callbacks = context.state.callbacks
    swe_deps = SWEDeps(**swe_deps_serializable_dict, callbacks=callbacks)
    swe_agent = SweAgentV1(swe_deps)
    swe_run_result = await swe_agent(prompt)
    await callbacks.add_result_to_queue(swe_deps.user_id, kvasir_run_id, swe_run_result)

    if await callbacks.get_run_status(swe_deps.user_id, kvasir_run_id) == "waiting":
        kvasir_v1 = await KvasirV1.from_run(swe_deps.user_id, kvasir_run_id, callbacks)
        async for _ in kvasir_v1("Continue processing results from the queue."):
            pass

    return swe_run_result


@v1_broker.task
async def resume_swe_run_from_orchestrator(
        user_id: UUID,
        swe_run_id: UUID,
        kvasir_run_id: UUID,
        message: str,
        time_limit: int,
        guidelines: List[SUPPORTED_TASKS_LITERAL],
        context: Annotated[Context, TaskiqDepends()]) -> str:

    callbacks: KvasirV1Callbacks = context.state.callbacks
    swe_agent = await SweAgentV1.from_run(user_id, swe_run_id, callbacks)
    swe_agent.update_time_limit(time_limit)
    swe_agent.update_guidelines(guidelines)
    swe_run_result = await swe_agent(message)
    await callbacks.add_result_to_queue(user_id, kvasir_run_id, swe_run_result)

    if await callbacks.get_run_status(user_id, kvasir_run_id) == "waiting":
        kvasir_v1 = await KvasirV1.from_run(user_id, kvasir_run_id, callbacks)
        async for _ in kvasir_v1("Continue processing results from the queue."):
            pass

    return swe_run_result


@v1_broker.task
async def start_analysis_run_from_orchestrator(
        prompt: str,
        kvasir_run_id: UUID,
        analysis_deps_serializable_dict: Dict,
        context: Annotated[Context, TaskiqDepends()]) -> str:

    callbacks: KvasirV1Callbacks = context.state.callbacks
    analysis_deps = AnalysisDeps(
        **analysis_deps_serializable_dict, callbacks=callbacks)
    analysis_agent = AnalysisAgentV1(deps=analysis_deps)
    analysis_run_result = await analysis_agent(prompt)
    await callbacks.add_result_to_queue(analysis_deps.user_id, kvasir_run_id, analysis_run_result)

    if await callbacks.get_run_status(analysis_deps.user_id, kvasir_run_id) == "waiting":
        kvasir_v1 = await KvasirV1.from_run(analysis_deps.user_id, kvasir_run_id, callbacks)
        async for _ in kvasir_v1("Continue processing results from the queue."):
            pass

    return analysis_run_result


@v1_broker.task
async def resume_analysis_run_from_orchestrator(
        user_id: UUID,
        analysis_run_id: UUID,
        kvasir_run_id: UUID,
        message: str,
        time_limit: int,
        guidelines: List[SUPPORTED_TASKS_LITERAL],
        context: Annotated[Context, TaskiqDepends()]) -> str:

    callbacks: KvasirV1Callbacks = context.state.callbacks
    analysis_agent = await AnalysisAgentV1.from_run(user_id, analysis_run_id, callbacks)
    analysis_agent.update_time_limit(time_limit)
    analysis_agent.update_guidelines(guidelines)
    analysis_run_result = await analysis_agent(message)
    await callbacks.add_result_to_queue(user_id, kvasir_run_id, analysis_run_result)

    if await callbacks.get_run_status(user_id, kvasir_run_id) == "waiting":
        kvasir_v1 = await KvasirV1.from_run(user_id, kvasir_run_id, callbacks)
        async for _ in kvasir_v1("Continue processing results from the queue."):
            pass

    return analysis_run_result


model = get_model()


kvasir_v1_agent = Agent[KvasirV1Deps, KvasirOutput](
    model,
    deps_type=KvasirV1Deps,
    toolsets=[navigation_toolset, knowledge_bank_toolset],
    retries=3,
    model_settings=ModelSettings(temperature=0),
    output_type=submit_kvasir_response
)


@kvasir_v1_agent.system_prompt
async def kvasir_v1_system_prompt(ctx: RunContext[KvasirV1Deps]) -> str:
    ls, ls_err = await ctx.deps.sandbox.list_directory_contents()

    if ls_err:
        raise RuntimeError(
            f"Failed to list working directory contents: {ls_err}")

    current_wd = f"ls out:\n{ls}\n\n"
    folder_structure = await ctx.deps.sandbox.get_folder_structure()
    env_description = ctx.deps.sandbox.get_pyproject_for_env_description()
    project_description = await ctx.deps.ontology.describe_mount_group()

    full_system_prompt = (
        f"{KVASIR_V1_SYSTEM_PROMPT}\n\n" +
        f"Project description: {project_description}\n\n" +
        f"Current working directory: {current_wd}\n\n" +
        f"Folder structure: {folder_structure}\n\n" +
        f"You environment is described by the following pyproject.toml:\n\n<pyproject>\n{env_description}\n</pyproject>\n\n"
    )

    return full_system_prompt


class KvasirV1(AgentV1[KvasirV1Deps, KvasirOutput]):
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

    async def __call__(self, prompt: str) -> AsyncGenerator[Tuple[KvasirOutput, bool], None]:

        try:
            await self._setup_run()
            results_queue = await self.deps.callbacks.get_results_queue(self.deps.user_id, self.deps.run_id)
            first = True
            prompt = (
                f"This is the current state of the results queue:\n\n" +
                f"<results_queue>\n{'\n\n'.join(results_queue)}\n</results_queue>\n\n" +
                f"Now, take your actions based on the results. "
                f"The user prompt is:\n\n<user_prompt>\n{prompt}\n</user_prompt>"
            )

            while results_queue or first:
                async for output, last in self._run_agent_streaming(prompt):
                    yield output, last

                output: KvasirOutput = output

                for analysis_run_to_launch in output.analysis_runs_to_launch:
                    base_deps_dict = self.deps.to_dict()
                    valid_fields = {f.name for f in fields(AnalysisDeps)}
                    analysis_deps_dict = {
                        k: v for k, v in base_deps_dict.items()
                        if k in valid_fields
                    }
                    analysis_deps_dict.update({
                        "kvasir_run_id": self.deps.run_id,
                        "data_paths": analysis_run_to_launch.data_paths,
                        "injected_analyses": analysis_run_to_launch.analyses_to_inject,
                        "time_limit": analysis_run_to_launch.time_limit,
                        "notebook": OrderedDict(),
                        "guidelines": analysis_run_to_launch.guidelines,
                        "run_name": analysis_run_to_launch.run_name,
                        "run_id": None,
                    })
                    if analysis_run_to_launch.analysis_id is not None:
                        analysis_deps_dict["analysis_id"] = analysis_run_to_launch.analysis_id
                    await start_analysis_run_from_orchestrator.kiq(
                        prompt=analysis_run_to_launch.deliverable_description,
                        kvasir_run_id=self.deps.run_id,
                        analysis_deps_serializable_dict=analysis_deps_dict
                    )

                for analysis_run_to_resume in output.analysis_runs_to_resume:
                    await resume_analysis_run_from_orchestrator.kiq(
                        user_id=self.deps.user_id,
                        analysis_run_id=analysis_run_to_resume.run_id,
                        kvasir_run_id=self.deps.run_id,
                        message=analysis_run_to_resume.message,
                        time_limit=analysis_run_to_resume.time_limit,
                        guidelines=analysis_run_to_resume.guidelines if analysis_run_to_resume.guidelines else [],
                    )

                for swe_run_to_launch in output.swe_runs_to_launch:
                    base_deps_dict = self.deps.to_dict()
                    valid_fields = {f.name for f in fields(SWEDeps)}
                    swe_deps_dict = {
                        k: v for k, v in base_deps_dict.items()
                        if k in valid_fields
                    }
                    swe_deps_dict.update({
                        "kvasir_run_id": self.deps.run_id,
                        "data_paths": swe_run_to_launch.data_paths,
                        "injected_analyses": swe_run_to_launch.analyses_to_inject,
                        "injected_swe_runs": swe_run_to_launch.swe_runs_to_inject,
                        "read_only_paths": swe_run_to_launch.read_only_paths,
                        "time_limit": swe_run_to_launch.time_limit,
                        "guidelines": swe_run_to_launch.guidelines,
                        "modified_files": {},
                        "run_name": swe_run_to_launch.run_name,
                        "run_id": None,
                    })
                    await start_swe_run_from_orchestrator.kiq(
                        prompt=swe_run_to_launch.deliverable_description,
                        kvasir_run_id=self.deps.run_id,
                        swe_deps_serializable_dict=swe_deps_dict
                    )

                for swe_run_to_resume in output.swe_runs_to_resume:
                    await resume_swe_run_from_orchestrator.kiq(
                        user_id=self.deps.user_id,
                        swe_run_id=swe_run_to_resume.run_id,
                        kvasir_run_id=self.deps.run_id,
                        message=swe_run_to_resume.message,
                        time_limit=swe_run_to_resume.time_limit,
                        guidelines=swe_run_to_resume.guidelines if swe_run_to_resume.guidelines else [],
                    )

                await self.deps.callbacks.pop_result_from_queue(self.deps.user_id, self.deps.run_id)
                results_queue = await self.deps.callbacks.get_results_queue(self.deps.user_id, self.deps.run_id)
                first = False

                prompt = (
                    "This is the current state of the results queue:\n\n" +
                    f"<results_queue>{'\n\n'.join(results_queue)}</results_queue>\n\n" +
                    "Now, take your actions based on the results. "
                )

            await self.finish_run("Kvasir run completed")
            await self.deps.callbacks.set_run_status(self.deps.user_id, self.deps.run_id, "waiting")

        except Exception as e:
            await self.fail_run_if_exists(f"Error running orchestrator: {e}")
            raise e
