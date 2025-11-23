from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_ai import RunContext
from pydantic_ai.exceptions import ModelRetry

from kvasir_research.agents.v1.kvasir.knowledge_bank import SUPPORTED_TASKS_LITERAL
from kvasir_research.agents.v1.kvasir.deps import KvasirV1Deps
from kvasir_research.agents.v1.base_agent import Context


class AnalysisRunToLaunch(BaseModel):
    run_name: str
    deliverable_description: str
    data_paths: List[str]
    entities_to_inject: Context = Context()
    # input_entities: List[UUID] = Field(default_factory=list)
    guidelines: List[SUPPORTED_TASKS_LITERAL] = Field(default_factory=list)
    time_limit: int
    # associate with existing analysis, or create a new one
    analysis_id: Optional[UUID] = None


class AnalysisRunToResume(BaseModel):
    run_id: UUID
    message: str
    entities_to_inject: Context = Context()
    guidelines: List[SUPPORTED_TASKS_LITERAL] = Field(default_factory=list)
    time_limit: int


class SWERunToLaunch(BaseModel):
    run_name: str
    deliverable_description: str
    read_only_paths: List[str]
    data_paths: List[str]
    entities_to_inject: Context = Context()
    # input_entities: List[UUID] = Field(default_factory=list)
    guidelines: List[SUPPORTED_TASKS_LITERAL] = Field(default_factory=list)
    time_limit: int
    # associate with existing pipeline, or create a new one
    pipeline_id: Optional[UUID] = None


class SWERunToResume(BaseModel):
    run_id: UUID
    message: str
    guidelines: List[SUPPORTED_TASKS_LITERAL] = Field(default_factory=list)
    entities_to_inject: Context = Context()
    time_limit: int


class DispatchAgentsOutput(BaseModel):
    analysis_runs_to_launch: List[AnalysisRunToLaunch] = []
    analysis_runs_to_resume: List[AnalysisRunToResume] = []
    swe_runs_to_launch: List[SWERunToLaunch] = []
    swe_runs_to_resume: List[SWERunToResume] = []
    completed: bool = False


async def dispatch_agents(ctx: RunContext[KvasirV1Deps], output: DispatchAgentsOutput) -> DispatchAgentsOutput:
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Dispatching agents: {len(output.analysis_runs_to_launch)} analysis runs to launch, {len(output.analysis_runs_to_resume)} to resume, {len(output.swe_runs_to_launch)} SWE runs to launch, {len(output.swe_runs_to_resume)} to resume", "tool_call")

    # Validate that resumed runs are in the correct launched run lists
    for analysis_run_to_resume in output.analysis_runs_to_resume:
        if analysis_run_to_resume.run_id not in ctx.deps.launched_analysis_run_ids:
            # Check if it's trying to resume a SWE run as an analysis run
            if analysis_run_to_resume.run_id in ctx.deps.launched_swe_run_ids:
                raise ModelRetry(
                    f"Analysis run {analysis_run_to_resume.run_id} is a SWE run, not an analysis run. Cannot resume SWE runs as analysis runs.")
            raise ModelRetry(
                f"Analysis run {analysis_run_to_resume.run_id} not in launched analysis run IDs list. Full IDs must be used, choose between {ctx.deps.launched_analysis_run_ids}")

        if analysis_run_to_resume.entities_to_inject.get_num_entities() > ctx.deps.max_entities_in_context:
            raise ModelRetry(
                f"You can maximally inject {ctx.deps.max_entities_in_context} entities in the analysis agent's context. ")

        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Resuming analysis run {analysis_run_to_resume.run_id}", "tool_call")

    for swe_run_to_resume in output.swe_runs_to_resume:
        if swe_run_to_resume.run_id not in ctx.deps.launched_swe_run_ids:
            # Check if it's trying to resume an analysis run as a SWE run
            if swe_run_to_resume.run_id in ctx.deps.launched_analysis_run_ids:
                raise ModelRetry(
                    f"SWE run {swe_run_to_resume.run_id} is an analysis run, not a SWE run. Cannot resume analysis runs as SWE runs.")
            raise ModelRetry(
                f"SWE run {swe_run_to_resume.run_id} not in launched SWE run IDs list. Full IDs must be used, choose between {ctx.deps.launched_swe_run_ids}")

        if swe_run_to_resume.entities_to_inject.get_num_entities() > ctx.deps.max_entities_in_context:
            raise ModelRetry(
                f"You can maximally inject {ctx.deps.max_entities_in_context} entities in the SWE agent's context. ")

        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Resuming SWE run {swe_run_to_resume.run_id}", "tool_call")

    for analysis_run_to_launch in output.analysis_runs_to_launch:
        if analysis_run_to_launch.entities_to_inject.get_num_entities() > ctx.deps.max_entities_in_context:
            raise ModelRetry(
                f"You can maximally inject {ctx.deps.max_entities_in_context} entities in the analysis agent's context. ")
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Launching analysis run {analysis_run_to_launch.run_name}", "tool_call")

    for swe_run_to_launch in output.swe_runs_to_launch:
        if swe_run_to_launch.entities_to_inject.get_num_entities() > ctx.deps.max_entities_in_context:
            raise ModelRetry(
                f"You can maximally inject {ctx.deps.max_entities_in_context} entities in the SWE agent's context. ")
        await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Launching SWE run {swe_run_to_launch.run_name}", "tool_call")

    total_launched = len(output.analysis_runs_to_launch) + \
        len(output.swe_runs_to_launch)
    total_resumed = len(output.analysis_runs_to_resume) + \
        len(output.swe_runs_to_resume)
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Successfully dispatched {total_launched} new run(s) and {total_resumed} resumed run(s)", "result")
    return DispatchAgentsOutput(**output.model_dump())


async def read_entities(ctx: RunContext[KvasirV1Deps], entities: List[UUID]) -> str:
    """
    Read the details of one or more entities in the graph. 
    The entities are data sources, datasets, analyses, pipelines, or models.
    """
    new_entities = set(entities)
    union_entities = ctx.deps.entities_in_context | new_entities

    if len(union_entities) > ctx.deps.max_entities_in_context:
        raise ModelRetry(
            f"Max entities in context reached: {len(union_entities)} > {ctx.deps.max_entities_in_context}. You can ask the user to remove some. ")

    ctx.deps.entities_in_context.update(new_entities)

    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Reading details for {len(entities)} entity/ies", "tool_call")
    descriptions = await ctx.deps.ontology.describe_entities(list(ctx.deps.entities_in_context))
    await ctx.deps.callbacks.log(ctx.deps.user_id, ctx.deps.run_id, f"Retrieved entity details ({len(descriptions)} characters)", "result")
    descriptions = f"<entity_context>\n\n{descriptions}\n\n</entity_context>"

    return descriptions
