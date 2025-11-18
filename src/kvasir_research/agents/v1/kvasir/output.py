from typing import List
from uuid import UUID
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


async def submit_kvasir_response(ctx: RunContext[KvasirV1Deps], output: OrchestratorOutput) -> OrchestratorOutput:
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

    return output
