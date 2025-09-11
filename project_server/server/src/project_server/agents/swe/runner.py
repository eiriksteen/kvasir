import uuid
from typing import Literal, Optional
from datetime import datetime, timezone
import docker
from pathlib import Path
from pydantic_ai.agent import AgentRunResult

from project_server.redis import get_redis
from project_server.agents.swe.agent import swe_agent
from project_server.agents.swe.output import (
    SWEAgentOutput,
    PlanningOutput,
    ImplementationOutputFull,
    SetupAgentOutputWithScript,
    submit_setup_output,
    submit_implementation_output,
    ConfigOutput
)
from project_server.agents.swe.deps import SWEAgentDeps
from project_server.utils.code_utils import run_shell_code_in_container
from project_server.worker import logger
from project_server.app_secrets import SWE_MAX_TRIES
from project_server.client import (
    ProjectClient,
    post_run,
    post_run_message,
    post_run_message_pydantic,
    patch_run_status
)
from synesis_schemas.main_server import (
    RunCreate,
    RunMessageCreate,
    RunMessageCreatePydantic,
    RunStatusUpdate
)


class SWEAgentRunner:

    def __init__(
            self,
            user_id: str,
            bearer_token: str,
            conversation_id: Optional[uuid.UUID] = None,
            parent_run_id: Optional[uuid.UUID] = None,
            log_to_parent_run: bool = True,
            run_id: Optional[uuid.UUID] = None,
            create_new_container_on_start: bool = False,
            create_new_container_on_package_installation: bool = True,
            log=False
    ):

        self.swe_agent = swe_agent
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.parent_run_id = parent_run_id
        self.run_id = run_id
        self.message_history = []
        self.deps = None
        self.plan_result = None
        self.setup_result = None
        self.config_result = None
        self.implementation_result = None
        self.container = None
        self.log = log
        self.max_tries = SWE_MAX_TRIES
        self.tries = 0
        self.container_name = "project-sandbox"
        self.container_cwd = Path("/app") / f"{uuid.uuid4()}"
        # TODO: Implement these
        self.create_new_container_on_start = create_new_container_on_start
        self.create_new_container_on_package_installation = create_new_container_on_package_installation
        self.new_container_created = False
        ##
        self.base_image = "project-sandbox"
        self.docker_client = docker.from_env()
        self.log_to_parent_run = log_to_parent_run
        self.redis_stream = get_redis()
        self.project_client = ProjectClient()
        self.project_client.set_bearer_token(bearer_token)
        self.deps = SWEAgentDeps(
            cwd=str(self.container_cwd),
            container_name=self.container_name,
            test_code_to_append_to_implementation=None
        )

    async def __call__(
        self,
        prompt_content: str,
        test_code_to_append_to_implementation: Optional[str] = None
    ) -> SWEAgentOutput:

        try:
            if self.run_id is None:
                if self.log:
                    logger.info(
                        f"Creating new SWE run for conversation {self.conversation_id} and parent run {self.parent_run_id}")
                run = await post_run(self.project_client, RunCreate(
                    type="swe",
                    conversation_id=self.conversation_id,
                    parent_run_id=self.parent_run_id
                ))
                self.run_id = run.id

            await self._setup_container()
            self.deps.test_code_to_append_to_implementation = test_code_to_append_to_implementation

            swe_prompt = (
                f"Your instruction is:\n\n'{prompt_content}'\n\n" +
                "Now choose your action. Create an implementation plan, write the setup script, write the config script, or the final implementation. " +
                "In case you have been provided feedback, choose your action based on it. Only redo the steps deemed necessary by the feedback." +
                "NB: The setup script must be written and completed before the final implementation."
            )

            self.implementation_result = None

            while not self.implementation_result:

                if self.tries >= self.max_tries:
                    raise RuntimeError(
                        f"SWE agent failed to implement function after {self.max_tries} tries")

                self.tries += 1

                run_result = await self.swe_agent.run(
                    swe_prompt,
                    output_type=[
                        PlanningOutput,
                        # TODO: Add setup, will need to spin up extra container in this case
                        # submit_setup_output,
                        ConfigOutput,
                        submit_implementation_output
                    ],
                    deps=self.deps,
                    message_history=self.message_history
                )

                self.message_history += run_result.new_messages()

                if isinstance(run_result.output, PlanningOutput):
                    self.plan_result = run_result
                    if self.log:
                        await self._log_message_to_redis("Plan complete", "result")
                        logger.info(f"Plan result: {self.plan_result}")

                # elif isinstance(run_result.output, SetupAgentOutputWithScript):
                #     self.setup_result = run_result
                #     await self._install_python_version(run_result.output.python_version)
                #     await self._run_setup_script(run_result.output.script)
                #     if self.log:
                #         await self._log_message_to_redis("Setup complete", "result")
                #         logger.info(f"Setup result: {self.setup_result}")

                elif isinstance(run_result.output, ConfigOutput):
                    self.config_result = run_result
                    if self.log:
                        await self._log_message_to_redis("Config complete", "result")
                        logger.info(f"Config result: {self.config_result}")

                elif isinstance(run_result.output, ImplementationOutputFull):
                    self.implementation_result = run_result
                    if self.log:
                        await self._log_message_to_redis(
                            "Implementation complete", "result")
                        logger.info(
                            f"Implementation result: {self.implementation_result}")

                else:
                    raise RuntimeError(
                        f"Unrecognized agent return type: {run_result.output}")

                swe_prompt = "Choose your action"

            # We only save the run messages as the outputs are dealt with by the caller

        except Exception as e:
            # await self._save_results()
            if self.log:
                await self._log_message_to_redis(f"Error running SWE agent: {e}", "error", write_to_db=True)
                logger.error(f"Error running SWE agent: {e}")
            await patch_run_status(self.project_client, RunStatusUpdate(
                run_id=self.run_id,
                status="failed"
            ))
            if self.container and self.new_container_created:
                self.container.stop()
                self.container.remove()
                self.new_container_created = False
            raise e

        else:
            await self._save_results()
            return SWEAgentOutput(
                plan=self.plan_result.output if self.plan_result else None,
                setup=self.setup_result.output if self.setup_result else None,
                config=self.config_result.output if self.config_result else None,
                implementation=self.implementation_result.output
            )

    async def _log_message_to_redis(
            self,
            content: str,
            message_type: Literal["tool_call", "result", "error"],
            write_to_db: bool = True
    ):
        """Log a message to Redis stream"""

        log_run_id = self.parent_run_id if self.log_to_parent_run and self.parent_run_id else self.run_id

        message = {
            "id": str(uuid.uuid4()),
            "role": "agent",
            "content": content,
            "run_id": str(log_run_id),
            "type": message_type,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.redis_stream.xadd(str(log_run_id), message)

        if write_to_db:
            run_message = RunMessageCreate(
                type=message_type,
                run_id=log_run_id,
                content=content
            )
            await post_run_message(self.project_client, run_message)

    async def _setup_container(self) -> None:

        if self.container is not None:
            return

        if self.log:
            await self._log_message_to_redis("Setting up Docker container for SWE agent...", "tool_call")

        if self.create_new_container_on_start:
            # Is now sync, blocking the main thread, TODO: Make async
            self.container = self.docker_client.containers.create(
                self.base_image,
                name=self.container_name
            )

            self.container.start()
            self.new_container_created = True

        else:
            try:
                self.container = self.docker_client.containers.get(
                    self.container_name)
            except docker.errors.NotFound:
                self.container = self.docker_client.containers.create(
                    self.base_image,
                    name=self.container_name
                )
                self.container.start()

        _, err = await run_shell_code_in_container(
            f"mkdir -p {str(self.container_cwd)}",
            container_name=self.container_name
        )

        if err:
            if self.log:
                await self._log_message_to_redis(f"Error creating directory: {err}", "result")
            raise RuntimeError(f"Error creating directory: {err}")

        await self._log_message_to_redis("Docker container started successfully", "result")

    async def _install_python_version(self, python_version: str) -> None:
        if self.log:
            await self._log_message_to_redis(f"Installing Python version: {python_version}", "tool_call")

        check_output, _ = await run_shell_code_in_container(
            f"pyenv versions | grep {python_version}",
            container_name=self.container_name
        )

        if not check_output.strip():
            out, err = await run_shell_code_in_container(
                f"pyenv install {python_version}",
                container_name=self.container_name
            )

            if err:
                if self.log:
                    await self._log_message_to_redis(f"Error installing Python version: {err}", "result")
                raise RuntimeError(f"Error installing python version: {err}")

        out, err = await run_shell_code_in_container(
            f"pyenv global {python_version}",
            container_name=self.container_name
        )

        if err:
            if self.log:
                await self._log_message_to_redis(f"Error setting global Python version: {err}", "result")
            raise RuntimeError(f"Error setting global python version: {err}")

        if self.log:
            await self._log_message_to_redis(f"Python {python_version} installed and set as global version", "result")

        return out

    async def _run_setup_script(self, setup_script: str) -> None:
        if self.log:
            await self._log_message_to_redis("Running setup script...", "tool_call")

        out, err = await run_shell_code_in_container(
            setup_script,
            container_name=self.container_name,
            cwd=str(self.container_cwd)
        )

        if err:
            if self.log:
                await self._log_message_to_redis(f"Error running setup script: {err}", "result")
            raise RuntimeError(f"Error running setup script: {err}")

        if self.log:
            await self._log_message_to_redis("Setup script run successfully", "result")

        return out

    async def _save_results(self):

        assert self.implementation_result is not None, "Cannot save results before implementation is complete."

        if self.plan_result is not None:
            await post_run_message_pydantic(self.project_client, RunMessageCreatePydantic(
                run_id=self.run_id,
                content=self.plan_result.new_messages_json()
            ))

        if self.setup_result is not None:
            await post_run_message_pydantic(self.project_client, RunMessageCreatePydantic(
                run_id=self.run_id,
                content=self.setup_result.new_messages_json()
            ))

        if self.config_result is not None:
            await post_run_message_pydantic(self.project_client, RunMessageCreatePydantic(
                run_id=self.run_id,
                content=self.config_result.new_messages_json()
            ))

        await post_run_message_pydantic(self.project_client, RunMessageCreatePydantic(
            run_id=self.run_id,
            content=self.implementation_result.new_messages_json()
        ))
