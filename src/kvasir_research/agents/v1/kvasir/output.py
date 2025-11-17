from typing import List
from uuid import uuid4, UUID
from pydantic import BaseModel
from pydantic_ai import RunContext
from pydantic_ai.exceptions import ModelRetry

from kvasir_research.agents.abstract_agent import AbstractAgentOutput
from kvasir_research.agents.v1.kvasir.knowledge_bank import SUPPORTED_TASKS_LITERAL
from kvasir_research.agents.v1.kvasir.deps import KvasirV1Deps


class AnalysisRunToLaunch(BaseModel):
    run_name: str
    deliverable_description: str
    data_paths: List[str]
    analyses_to_inject: List[UUID] = []
    guidelines: List[SUPPORTED_TASKS_LITERAL] = []
    time_limit: int


class AnalysisRunToLaunchWithId(AnalysisRunToLaunch):
    run_id: UUID


class AnalysisRunToResume(BaseModel):
    run_id: UUID
    message: str
    guidelines: List[SUPPORTED_TASKS_LITERAL] = []
    time_limit: int


class SWERunToLaunch(BaseModel):
    run_name: str
    deliverable_description: str
    read_only_paths: List[str]
    data_paths: List[str]
    analyses_to_inject: List[UUID] = []
    swe_runs_to_inject: List[UUID] = []
    guidelines: List[SUPPORTED_TASKS_LITERAL] = []
    time_limit: int


class SWERunToLaunchWithId(SWERunToLaunch):
    run_id: UUID


class SWERunToResume(BaseModel):
    run_id: UUID
    message: str
    guidelines: List[SUPPORTED_TASKS_LITERAL] = []
    time_limit: int


class OrchestratorOutput(AbstractAgentOutput):
    analysis_runs_to_launch: List[AnalysisRunToLaunch] = []
    analysis_runs_to_resume: List[AnalysisRunToResume] = []
    swe_runs_to_launch: List[SWERunToLaunch] = []
    swe_runs_to_resume: List[SWERunToResume] = []
    completed: bool = False


class OrchestratorOutputWithIds(OrchestratorOutput):
    analysis_runs_to_launch: List[AnalysisRunToLaunchWithId] = []
    analysis_runs_to_resume: List[AnalysisRunToResume] = []
    swe_runs_to_launch: List[SWERunToLaunchWithId] = []
    swe_runs_to_resume: List[SWERunToResume] = []


async def submit_kvasir_response(ctx: RunContext[KvasirV1Deps], output: OrchestratorOutput) -> OrchestratorOutputWithIds:
    # Validate that resumed runs are in the correct launched run lists
    for analysis_run_to_resume in output.analysis_runs_to_resume:
        if analysis_run_to_resume.run_id not in ctx.deps.launched_analysis_run_ids:
            # Check if it's trying to resume a SWE run as an analysis run
            if analysis_run_to_resume.run_id in ctx.deps.launched_swe_run_ids:
                raise ModelRetry(
                    f"Analysis run {analysis_run_to_resume.run_id} is a SWE run, not an analysis run. Cannot resume SWE runs as analysis runs.")
            raise ModelRetry(
                f"Analysis run {analysis_run_to_resume.run_id} not in launched analysis run IDs list. Full IDs must be used, choose between {ctx.deps.launched_analysis_run_ids}")

    for swe_run_to_resume in output.swe_runs_to_resume:
        if swe_run_to_resume.run_id not in ctx.deps.launched_swe_run_ids:
            # Check if it's trying to resume an analysis run as a SWE run
            if swe_run_to_resume.run_id in ctx.deps.launched_analysis_run_ids:
                raise ModelRetry(
                    f"SWE run {swe_run_to_resume.run_id} is an analysis run, not a SWE run. Cannot resume analysis runs as SWE runs.")
            raise ModelRetry(
                f"SWE run {swe_run_to_resume.run_id} not in launched SWE run IDs list. Full IDs must be used, choose between {ctx.deps.launched_swe_run_ids}")

    final_output = OrchestratorOutputWithIds(
        **{**output.model_dump(), "analysis_runs_to_launch": [], "swe_runs_to_launch": []}
    )

    for analysis_run_to_launch in output.analysis_runs_to_launch:
        analysis_run_with_id = AnalysisRunToLaunchWithId(
            run_id=uuid4(),
            **analysis_run_to_launch.model_dump()
        )
        final_output.analysis_runs_to_launch.append(analysis_run_with_id)
        ctx.deps.launched_analysis_run_ids.append(analysis_run_with_id.run_id)
    for swe_run_to_launch in output.swe_runs_to_launch:
        swe_run_with_id = SWERunToLaunchWithId(
            run_id=uuid4(),
            **swe_run_to_launch.model_dump()
        )
        final_output.swe_runs_to_launch.append(swe_run_with_id)
        ctx.deps.launched_swe_run_ids.append(swe_run_with_id.run_id)

    return final_output
