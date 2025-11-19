from uuid import UUID
from dataclasses import dataclass, field
from taskiq import Context, TaskiqDepends
from typing import List, Dict, Tuple, Literal, Annotated, AsyncGenerator, Optional
from pydantic import ValidationError
from pydantic_ai import Agent, RunContext, ModelSettings

from kvasir_research.agents.v1.broker import v1_broker
from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks
from kvasir_research.agents.v1.kvasir.knowledge_bank import SUPPORTED_TASKS_LITERAL
from kvasir_research.agents.v1.analysis.agent import AnalysisAgentV1
from kvasir_research.agents.v1.swe.agent import SweAgentV1
from kvasir_research.agents.v1.kvasir.deps import KvasirV1Deps
from kvasir_research.agents.v1.kvasir.output import KvasirOutput, submit_kvasir_response
from kvasir_research.agents.v1.base_agent import BaseAgent
from kvasir_research.agents.v1.data_model import RunCreate
from kvasir_research.agents.v1.shared_tools import navigation_toolset, knowledge_bank_toolset
from kvasir_research.agents.v1.kvasir.prompt import KVASIR_V1_SYSTEM_PROMPT
from kvasir_research.agents.v1.deps import AgentDeps
from kvasir_ontology.ontology import Ontology
from kvasir_research.utils.agent_utils import get_model


@dataclass(kw_only=True)
class AnalysisRunToStart(AgentDeps):
    kvasir_run_id: UUID
    deliverable_description: str
    data_paths: List[str]
    injected_analyses: List[UUID]
    time_limit: int
    guidelines: List[SUPPORTED_TASKS_LITERAL] = field(default_factory=list)


@dataclass(kw_only=True)
class AnalysisRunToResume(AgentDeps):
    message: str
    time_limit: int
    kvasir_run_id: UUID
    guidelines: List[SUPPORTED_TASKS_LITERAL] = field(default_factory=list)


@dataclass(kw_only=True)
class SWERunToStart(AgentDeps):
    kvasir_run_id: UUID
    deliverable_description: str
    data_paths: List[str]
    injected_analyses: List[UUID]
    injected_swe_runs: List[UUID]
    read_only_paths: List[str]
    time_limit: int
    guidelines: List[SUPPORTED_TASKS_LITERAL] = field(default_factory=list)


@dataclass(kw_only=True)
class SWERunToResume(AgentDeps):
    message: str
    time_limit: int
    kvasir_run_id: UUID
    guidelines: List[SUPPORTED_TASKS_LITERAL] = field(default_factory=list)


@v1_broker.task
async def _start_swe_run_from_orchestrator(swe_run: SWERunToStart, context: Annotated[Context, TaskiqDepends()]) -> str:
    callbacks: KvasirV1Callbacks = context.state.callbacks

    swe_agent = SweAgentV1(
        user_id=swe_run.user_id,
        project_id=swe_run.project_id,
        package_name=swe_run.package_name,
        sandbox_type=swe_run.sandbox_type,
        callbacks=callbacks,
        bearer_token=swe_run.bearer_token
    )

    await swe_agent.create_deps(
        kvasir_run_id=swe_run.kvasir_run_id,
        run_name=swe_run.run_name,
        data_paths=swe_run.data_paths,
        injected_analyses=swe_run.injected_analyses,
        injected_swe_runs=swe_run.injected_swe_runs,
        read_only_paths=swe_run.read_only_paths,
        time_limit=swe_run.time_limit,
        guidelines=swe_run.guidelines,
    )

    swe_run_result = await swe_agent(swe_run.deliverable_description)

    await callbacks.add_result_to_queue(swe_run.user_id, swe_run.kvasir_run_id, swe_run_result)

    if await callbacks.get_run_status(swe_run.user_id, swe_run.kvasir_run_id) == "waiting":
        kvasir_v1 = KvasirV1(
            user_id=swe_run.user_id,
            run_id=swe_run.kvasir_run_id,
            project_id=swe_run.project_id,
            package_name=swe_run.package_name,
            sandbox_type=swe_run.sandbox_type,
            callbacks=callbacks,
            bearer_token=swe_run.bearer_token
        )
        async for _ in kvasir_v1("Continue processing results from the queue."):
            pass

    return swe_run_result


@v1_broker.task
async def _resume_swe_run_from_orchestrator(swe_run: SWERunToResume, context: Annotated[Context, TaskiqDepends()]) -> str:
    callbacks: KvasirV1Callbacks = context.state.callbacks

    swe_agent = SweAgentV1(
        user_id=swe_run.user_id,
        project_id=swe_run.project_id,
        package_name=swe_run.package_name,
        sandbox_type=swe_run.sandbox_type,
        callbacks=callbacks,
        bearer_token=swe_run.bearer_token,
        run_id=swe_run.run_id,
    )

    await swe_agent.load_deps_from_run(
        swe_run.run_id,
        guidelines=swe_run.guidelines if swe_run.guidelines else None,
        time_limit=swe_run.time_limit,
    )

    swe_run_result = await swe_agent(swe_run.message)

    await callbacks.add_result_to_queue(swe_run.user_id, swe_run.kvasir_run_id, swe_run_result)

    if await callbacks.get_run_status(swe_run.user_id, swe_run.kvasir_run_id) == "waiting":
        kvasir_v1 = KvasirV1(
            user_id=swe_run.user_id,
            run_id=swe_run.kvasir_run_id,
            project_id=swe_run.project_id,
            package_name=swe_run.package_name,
            sandbox_type=swe_run.sandbox_type,
            callbacks=callbacks,
            bearer_token=swe_run.bearer_token
        )
        async for _ in kvasir_v1("Continue processing results from the queue."):
            pass

    return swe_run_result


@v1_broker.task
async def _start_analysis_run_from_orchestrator(analysis_run: AnalysisRunToStart, context: Annotated[Context, TaskiqDepends()]) -> str:
    callbacks: KvasirV1Callbacks = context.state.callbacks

    analysis_agent = AnalysisAgentV1(
        user_id=analysis_run.user_id,
        project_id=analysis_run.project_id,
        package_name=analysis_run.package_name,
        sandbox_type=analysis_run.sandbox_type,
        callbacks=callbacks,
        bearer_token=analysis_run.bearer_token
    )

    await analysis_agent.create_deps(
        kvasir_run_id=analysis_run.kvasir_run_id,
        run_name=analysis_run.run_name,
        data_paths=analysis_run.data_paths,
        injected_analyses=analysis_run.injected_analyses,
        time_limit=analysis_run.time_limit,
        guidelines=analysis_run.guidelines,
    )

    analysis_run_result = await analysis_agent(analysis_run.deliverable_description)

    await callbacks.add_result_to_queue(analysis_run.user_id, analysis_run.kvasir_run_id, analysis_run_result)

    if await callbacks.get_run_status(analysis_run.user_id, analysis_run.kvasir_run_id) == "waiting":
        kvasir_v1 = KvasirV1(
            user_id=analysis_run.user_id,
            run_id=analysis_run.kvasir_run_id,
            project_id=analysis_run.project_id,
            package_name=analysis_run.package_name,
            sandbox_type=analysis_run.sandbox_type,
            callbacks=callbacks,
            bearer_token=analysis_run.bearer_token
        )
        async for _ in kvasir_v1("Continue processing results from the queue."):
            pass

    return analysis_run_result


@v1_broker.task
async def _resume_analysis_run_from_orchestrator(analysis_run: AnalysisRunToResume, context: Annotated[Context, TaskiqDepends()]) -> str:
    callbacks: KvasirV1Callbacks = context.state.callbacks

    analysis_agent = AnalysisAgentV1(
        user_id=analysis_run.user_id,
        project_id=analysis_run.project_id,
        package_name=analysis_run.package_name,
        sandbox_type=analysis_run.sandbox_type,
        callbacks=callbacks,
        bearer_token=analysis_run.bearer_token,
        run_id=analysis_run.run_id,
    )

    await analysis_agent.load_deps_from_run(
        analysis_run.run_id,
        guidelines=analysis_run.guidelines if analysis_run.guidelines else None,
        time_limit=analysis_run.time_limit,
    )

    analysis_run_result = await analysis_agent(analysis_run.message)

    await callbacks.add_result_to_queue(analysis_run.user_id, analysis_run.kvasir_run_id, analysis_run_result)

    if await callbacks.get_run_status(analysis_run.user_id, analysis_run.kvasir_run_id) == "waiting":
        kvasir_v1 = KvasirV1(
            user_id=analysis_run.user_id,
            run_id=analysis_run.kvasir_run_id,
            project_id=analysis_run.project_id,
            package_name=analysis_run.package_name,
            sandbox_type=analysis_run.sandbox_type,
            callbacks=callbacks,
            bearer_token=analysis_run.bearer_token
        )
        async for _ in kvasir_v1("Continue processing results from the queue."):
            pass

    return analysis_run_result


model = get_model()


kvasir_v1_agent = Agent[KvasirV1Deps](
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


class KvasirV1(BaseAgent):
    def __init__(
        self,
        user_id: UUID,
        project_id: UUID,
        package_name: str,
        sandbox_type: Literal["local", "modal"],
        callbacks: KvasirV1Callbacks,
        bearer_token: Optional[str] = None,
        run_id: Optional[UUID] = None
    ):
        super().__init__(user_id, project_id, package_name,
                         sandbox_type, callbacks, bearer_token, run_id)
        self.callbacks = callbacks

    async def __call__(self, prompt: str) -> AsyncGenerator[Tuple[KvasirOutput, bool], None]:

        try:
            if self.run_id is None:
                run_create = RunCreate(
                    type="kvasir", project_id=self.project_id)
                self.run_id = (await self.callbacks.create_run(self.user_id, run_create)).id
                deps = KvasirV1Deps(
                    run_id=self.run_id,
                    project_id=self.project_id,
                    package_name=self.package_name,
                    user_id=self.user_id,
                    ontology=self.ontology,
                    sandbox_type=self.sandbox_type,
                    callbacks=self.callbacks,
                    bearer_token=self.bearer_token
                )
                await self.callbacks.save_deps(self.user_id, self.run_id, _orchestrator_deps_to_dict(deps), "kvasir")
            else:
                try:
                    deps_dict = await self.callbacks.load_deps(self.user_id, self.run_id, "kvasir")
                    deps = _orchestrator_dict_to_deps(
                        deps_dict, self.callbacks, self.ontology)
                except:
                    deps = KvasirV1Deps(
                        run_id=self.run_id,
                        project_id=self.project_id,
                        package_name=self.package_name,
                        user_id=self.user_id,
                        ontology=self.ontology,
                        sandbox_type=self.sandbox_type,
                        callbacks=self.callbacks,
                        bearer_token=self.bearer_token)
                    await self.callbacks.save_deps(self.user_id, self.run_id, _orchestrator_deps_to_dict(deps), "kvasir")

            await self.callbacks.set_run_status(self.user_id, self.run_id, "running")

            results_queue = await self.callbacks.get_results_queue(self.user_id, self.run_id)
            first = True
            prompt = (
                f"This is the current state of the results queue:\n\n" +
                f"<results_queue>\n{'\n\n'.join(results_queue)}\n</results_queue>\n\n" +
                f"Now, take your actions based on the results. "
                f"The user prompt is:\n\n<user_prompt>\n{prompt}\n</user_prompt>"
            )

            while results_queue or first:
                async with kvasir_v1_agent.run_stream(
                    prompt,
                    deps=deps,
                    message_history=await self.callbacks.get_message_history(self.user_id, self.run_id)
                ) as orchestrator_run:
                    async for message, last in orchestrator_run.stream_responses(debounce_by=0.01):
                        try:
                            output: KvasirOutput = await orchestrator_run.validate_response_output(
                                message,
                                allow_partial=not last
                            )
                            yield (output, last)
                        except ValidationError:
                            continue

                await self.callbacks.save_message_history(self.user_id, self.run_id, orchestrator_run.all_messages())
                if output is None:
                    raise RuntimeError(
                        "No valid output received from orchestrator")

                if output.completed:
                    await self.callbacks.set_run_status(self.user_id, self.run_id, "completed")
                    await self.callbacks.save_deps(self.user_id, self.run_id, _orchestrator_deps_to_dict(deps), "kvasir")
                    await self.callbacks.log(self.user_id, self.run_id, f"Orchestrator completed, cleaning up container for project {deps.project_id}", "result")
                    break

                for analysis_run_to_launch in output.analysis_runs_to_launch:
                    await _start_analysis_run_from_orchestrator.kiq(
                        AnalysisRunToStart(
                            run_name=analysis_run_to_launch.run_name,
                            kvasir_run_id=self.run_id,
                            deliverable_description=analysis_run_to_launch.deliverable_description,
                            data_paths=analysis_run_to_launch.data_paths,
                            injected_analyses=analysis_run_to_launch.analyses_to_inject,
                            time_limit=analysis_run_to_launch.time_limit,
                            guidelines=analysis_run_to_launch.guidelines,
                            user_id=self.user_id,
                            project_id=self.project_id,
                            package_name=self.package_name,
                            sandbox_type=self.sandbox_type,
                            bearer_token=self.bearer_token
                        )
                    )

                for analysis_run_to_resume in output.analysis_runs_to_resume:
                    await _resume_analysis_run_from_orchestrator.kiq(
                        AnalysisRunToResume(
                            run_id=analysis_run_to_resume.run_id,
                            message=analysis_run_to_resume.message,
                            time_limit=analysis_run_to_resume.time_limit,
                            guidelines=analysis_run_to_resume.guidelines if analysis_run_to_resume.guidelines else [],
                            kvasir_run_id=self.run_id,
                            user_id=self.user_id,
                            project_id=self.project_id,
                            package_name=self.package_name,
                            sandbox_type=self.sandbox_type,
                            bearer_token=self.bearer_token
                        )
                    )

                for swe_run_to_launch in output.swe_runs_to_launch:
                    await _start_swe_run_from_orchestrator.kiq(
                        SWERunToStart(
                            run_name=swe_run_to_launch.run_name,
                            kvasir_run_id=self.run_id,
                            deliverable_description=swe_run_to_launch.deliverable_description,
                            data_paths=swe_run_to_launch.data_paths,
                            injected_analyses=swe_run_to_launch.analyses_to_inject,
                            injected_swe_runs=swe_run_to_launch.swe_runs_to_inject,
                            read_only_paths=swe_run_to_launch.read_only_paths,
                            time_limit=swe_run_to_launch.time_limit,
                            guidelines=swe_run_to_launch.guidelines,
                            user_id=self.user_id,
                            project_id=self.project_id,
                            package_name=self.package_name,
                            sandbox_type=self.sandbox_type,
                            bearer_token=self.bearer_token
                        )
                    )

                for swe_run_to_resume in output.swe_runs_to_resume:
                    await _resume_swe_run_from_orchestrator.kiq(
                        SWERunToResume(
                            run_id=swe_run_to_resume.run_id,
                            message=swe_run_to_resume.message,
                            time_limit=swe_run_to_resume.time_limit,
                            guidelines=swe_run_to_resume.guidelines if swe_run_to_resume.guidelines else [],
                            kvasir_run_id=self.run_id,
                            user_id=self.user_id,
                            project_id=self.project_id,
                            package_name=self.package_name,
                            sandbox_type=self.sandbox_type,
                            bearer_token=self.bearer_token
                        )
                    )

                await self.callbacks.pop_result_from_queue(self.user_id, self.run_id)
                results_queue = await self.callbacks.get_results_queue(self.user_id, self.run_id)
                first = False

                prompt = (
                    "This is the current state of the results queue:\n\n" +
                    f"<results_queue>{'\n\n'.join(results_queue)}</results_queue>\n\n" +
                    "Now, take your actions based on the results. "
                )

                await self.callbacks.save_deps(self.user_id, self.run_id, _orchestrator_deps_to_dict(deps), "kvasir")
                await self.callbacks.set_run_status(self.user_id, self.run_id, "waiting")

        except Exception as e:
            if self.run_id:
                await self.callbacks.fail_run(self.user_id, self.run_id, f"Error running orchestrator: {e}")
            raise e


###


def _orchestrator_deps_to_dict(deps: KvasirV1Deps) -> Dict:
    return {
        "run_id": str(deps.run_id),
        "project_id": str(deps.project_id),
        "package_name": deps.package_name,
        "user_id": str(deps.user_id) if deps.user_id else None,
        "bearer_token": deps.bearer_token,
        "launched_analysis_run_ids": [str(x) for x in deps.launched_analysis_run_ids],
        "launched_swe_run_ids": [str(x) for x in deps.launched_swe_run_ids],
        "sandbox_type": deps.sandbox_type
    }


def _orchestrator_dict_to_deps(deps_dict: Dict, callbacks: KvasirV1Callbacks, ontology: Ontology) -> KvasirV1Deps:
    deps = KvasirV1Deps(
        run_id=UUID(deps_dict["run_id"]),
        project_id=UUID(deps_dict["project_id"]),
        package_name=deps_dict["package_name"],
        user_id=UUID(deps_dict["user_id"]) if deps_dict.get(
            "user_id") else None,
        ontology=ontology,
        launched_analysis_run_ids=[UUID(x) for x in deps_dict.get(
            "launched_analysis_run_ids", [])],
        launched_swe_run_ids=[UUID(x) for x in deps_dict.get(
            "launched_swe_run_ids", [])],
        sandbox_type=deps_dict.get("sandbox_type", "local"),
        callbacks=callbacks,
        bearer_token=deps_dict.get("bearer_token")
    )
    return deps
