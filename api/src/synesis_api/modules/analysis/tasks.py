from synesis_api.worker import broker
from synesis_api.modules.analysis.schema import AnalysisRequest, AnalysisJobResultMetadataInDB
from synesis_api.modules.analysis.agent.agent import analysis_agent


@broker.task
async def run_analysis_planner_task(
    analysis_request: AnalysisRequest,
) -> AnalysisJobResultMetadataInDB:
    return await analysis_agent.run_analysis_planner(analysis_request)


@broker.task
async def run_analysis_execution_task(
    analysis_request: AnalysisRequest,
) -> AnalysisJobResultMetadataInDB:
    return await analysis_agent.run_analysis_execution(analysis_request)