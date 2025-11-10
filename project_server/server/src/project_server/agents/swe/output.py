import shutil
from typing import List
from pydantic_ai import RunContext, ModelRetry
from pathlib import Path

from project_server.agents.swe.deps import SWEAgentDeps
from project_server.utils.code_utils import run_python_code_in_container
from project_server.utils.docker_utils import read_file_from_container
from project_server.agents.runner_base import StreamedCode
from project_server.client import post_swe_result_approval_request
from project_server.worker import logger
from synesis_schemas.project_server import ImplementationSummary, SWEOutput


async def submit_implementation_output(ctx: RunContext[SWEAgentDeps], result: SWEOutput) -> ImplementationSummary:

    testing_dirs: List[Path] = []

    main_script = await read_file_from_container(
        Path(result.main_script.path),
        ctx.deps.container_name
    )

    out, err = await run_python_code_in_container(result.main_script.content, container_name=ctx.deps.container_name)

    logger.info("MAIN SCRIPT")
    logger.info(main_script)
    logger.info("OUT")
    logger.info(out)
    logger.info("ERR")
    logger.info(err)

    for testing_dir in testing_dirs:
        shutil.rmtree(testing_dir, ignore_errors=True)

    if ctx.deps.log_code:
        await ctx.deps.log_code(StreamedCode(
            code=main_script,
            filename=Path(result.main_script.path).name,
            output=out,
            error=err
        ))

    if err:
        logger.info(f"Error executing code: {err}")
        raise ModelRetry(f"Error executing code: {err}")

    implementation_summary = ImplementationSummary(
        **result.model_dump(),
        conversation_id=ctx.deps.conversation_id,
        new_files=ctx.deps.new_files,
        modified_files=ctx.deps.modified_files,
        deleted_files=ctx.deps.deleted_files,
        renamed_files=ctx.deps.renamed_files)

    logger.info(
        f"Implementation summary: {implementation_summary.model_dump_json()}")

    feedback = await post_swe_result_approval_request(ctx.deps.client, implementation_summary)

    if not feedback.approved:
        raise ModelRetry(
            f"Submission rejected with feedback: {feedback.feedback}")

    return implementation_summary
