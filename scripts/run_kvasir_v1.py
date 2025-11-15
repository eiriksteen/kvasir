import asyncio
from uuid import uuid4, UUID
from typing import List, Literal
from collections import OrderedDict

# from kvasir_research.agents.abstract_callbacks import set_callbacks
from kvasir_research.secrets import PROJECTS_DIR
from kvasir_research.agents.kvasir_v1.agent import KvasirV1
from kvasir_research.agents.kvasir_v1.callbacks import KvasirV1Callbacks
from kvasir_research.agents.kvasir_v1.orchestrator import OrchestratorDeps, OrchestratorOutput
from kvasir_research.agents.kvasir_v1.swe import SWEDeps
from kvasir_research.agents.kvasir_v1.analysis import AnalysisDeps
from kvasir_research.agents.kvasir_v1.broker import logger
from kvasir_research.utils.redis_utils import (
    get_message_history as redis_get_message_history,
    save_message_history as redis_save_message_history,
    get_results_queue as redis_get_results_queue,
    pop_result_from_queue as redis_pop_result_from_queue,
    add_result_to_queue as redis_add_result_to_queue,
    save_deps as redis_save_deps,
    get_saved_deps as redis_get_saved_deps,
    set_run_status as redis_set_run_status,
    get_run_status as redis_get_run_status,
    save_swe_result as redis_save_swe_result,
    get_swe_result as redis_get_swe_result,
    save_analysis as redis_save_analysis,
    get_analysis as redis_get_analysis,
)


class RedisCallbacks(KvasirV1Callbacks):
    async def check_orchestrator_run_exists(self, run_id: UUID) -> bool:
        deps = await redis_get_saved_deps(str(run_id))
        return deps is None

    async def get_orchestrator_run_status(self, run_id: UUID) -> Literal["pending", "completed", "failed", "waiting", "running"]:
        status = await redis_get_run_status(str(run_id))
        return status if status else "pending"

    async def set_orchestrator_run_status(self, run_id: UUID, status: Literal["pending", "completed", "failed", "waiting", "running"]) -> str:
        await redis_set_run_status(str(run_id), status)
        return status

    async def get_results_queue(self, run_id: UUID) -> List[str]:
        return await redis_get_results_queue(str(run_id))

    async def pop_result_from_queue(self, run_id: UUID) -> str:
        return await redis_pop_result_from_queue(str(run_id))

    async def add_result_to_queue(self, run_id: UUID, result: str) -> None:
        await redis_add_result_to_queue(str(run_id), result)

    async def save_orchestrator_deps(self, run_id: UUID, deps: OrchestratorDeps) -> None:
        await redis_save_deps(str(run_id), deps)

    async def load_orchestrator_deps(self, run_id: UUID) -> OrchestratorDeps:
        deps_dict = await redis_get_saved_deps(str(run_id))
        if deps_dict is None:
            raise RuntimeError("Orchestrator deps not found")
        deps_dict["run_id"] = UUID(deps_dict["run_id"])
        deps_dict["project_id"] = UUID(deps_dict["project_id"])
        deps_dict["package_name"] = deps_dict.get(
            "package_name", "experiments")
        return OrchestratorDeps(**deps_dict)

    async def save_swe_deps(self, run_id: UUID, deps: SWEDeps) -> None:
        await redis_save_deps(str(run_id), deps)

    async def load_swe_deps(self, run_id: UUID) -> SWEDeps:
        deps_dict = await redis_get_saved_deps(str(run_id))
        if deps_dict is None:
            raise RuntimeError("SWE deps not found")
        deps_dict["orchestrator_id"] = UUID(deps_dict["orchestrator_id"])
        deps_dict["project_id"] = UUID(deps_dict["project_id"])
        return SWEDeps(**deps_dict)

    async def save_swe_result(self, run_id: UUID, result: str) -> None:
        await redis_save_swe_result(str(run_id), result)

    async def get_swe_result(self, run_id: UUID) -> str:
        res = await redis_get_swe_result(str(run_id))
        return res or ""

    async def save_analysis_deps(self, run_id: UUID, deps: AnalysisDeps) -> None:
        await redis_save_deps(str(run_id), deps)

    async def load_analysis_deps(self, run_id: UUID) -> AnalysisDeps:
        deps_dict = await redis_get_saved_deps(str(run_id))
        if deps_dict is None:
            raise RuntimeError("Analysis deps not found")
        deps_dict["orchestrator_id"] = UUID(deps_dict["orchestrator_id"])
        deps_dict["project_id"] = UUID(deps_dict["project_id"])
        # Ensure OrderedDict and tuple types for notebook
        notebook_raw = deps_dict.get("notebook", {})
        ordered = OrderedDict()
        for k, v in notebook_raw.items():
            if isinstance(v, list):
                ordered[k] = tuple(v)  # [type, content] -> (type, content)
            else:
                ordered[k] = v
        deps_dict["notebook"] = ordered
        return AnalysisDeps(**deps_dict)

    async def save_analysis_result(self, run_id: UUID, result: str) -> None:
        await redis_save_analysis(str(run_id), result)

    async def get_analysis_result(self, run_id: UUID) -> str:
        res = await redis_get_analysis(str(run_id))
        return res or ""

    async def save_message_history(self, run_id: UUID, message_history):
        await redis_save_message_history(str(run_id), message_history)

    async def get_message_history(self, run_id: UUID):
        return await redis_get_message_history(str(run_id))

    async def log(self, run_id: UUID, message: str) -> None:
        logger.info(f"[{run_id}] {message}")


async def main(project_name: str, sandbox_type: Literal["local", "modal"] = "local") -> List[OrchestratorOutput]:
    run_id = uuid4()
    project_id = uuid4()
    package_name = "experiments"

    agent = KvasirV1(
        run_id=run_id,
        project_id=project_id,
        package_name=package_name,
        sandbox_type=sandbox_type,
        callbacks=RedisCallbacks()
    )

    project_dir = PROJECTS_DIR / project_name
    with open(project_dir / "description.txt", "r") as f:
        description = f.read()
    data_dir = project_dir / "data"

    prompt = (
        f"{description}\n\n"
        f"The data is available at: {data_dir}"
    )

    outputs = await agent(prompt)
    return outputs


if __name__ == "__main__":
    project_name = "weather_forecasting"
    asyncio.run(main(project_name, "modal"))
