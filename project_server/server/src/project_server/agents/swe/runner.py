import uuid
import docker
from typing import Optional, List
from dataclasses import dataclass
from pathlib import Path

from project_server.agents.swe.agent import swe_agent
from project_server.agents.swe.output import (
    SWEAgentOutput,
    PlanningOutput,
    ImplementationOutputFull,
    # SetupAgentOutputWithScript,
    # submit_setup_output,
    submit_implementation_output,
    ConfigOutput
)
from project_server.agents.swe.deps import SWEAgentDeps, ScriptToInject
from project_server.utils.code_utils import run_shell_code_in_container
from project_server.agents.runner_base import RunnerBase
from project_server.entity_manager import file_manager


class SWEAgentRunner(RunnerBase):

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
            log=False,
            structure_ids_to_inject: Optional[List[str]] = None,
            inject_synthetic_data_descriptions: bool = False,
            scripts_to_inject: Optional[List[ScriptToInject]] = None
    ):

        super().__init__(
            agent=swe_agent,
            user_id=user_id,
            bearer_token=bearer_token,
            run_id=run_id,
            run_type="swe",
            conversation_id=conversation_id,
            parent_run_id=parent_run_id,
            log_to_parent_run=log_to_parent_run
        )

        self.plan_result = None
        self.setup_result = None
        self.config_result = None
        self.implementation_result = None
        self.container = None
        self.log = log
        self.container_name = "project-sandbox"
        self.container_cwd = Path("/app")
        self.scripts_to_inject = scripts_to_inject
        self.structure_ids_to_inject = structure_ids_to_inject
        self.inject_synthetic_data_descriptions = inject_synthetic_data_descriptions
        # TODO: Implement these
        self.create_new_container_on_start = create_new_container_on_start
        self.create_new_container_on_package_installation = create_new_container_on_package_installation
        self.new_container_created = False
        ##
        self.base_image = "project-sandbox"
        self.docker_client = docker.from_env()
        # Slightly annoying that we set it here, but the state of the deps must be maintained across calls,
        # and the agent changes variables during tool calls which should be maintained
        self.deps = self._prepare_deps()

    async def __call__(
        self,
        prompt_content: str,
        test_code_to_append_to_implementation: Optional[str] = None
    ) -> SWEAgentOutput:

        try:
            await self._create_run_if_not_exists()
            await self._setup_container()
            self.deps.test_code_to_append_to_implementation = test_code_to_append_to_implementation

            swe_prompt = (
                f"Your instruction is:\n\n'{prompt_content}'\n\n" +
                "Now choose your action. Create an implementation plan, write the setup script, write the config script, or the final implementation. " +
                "In case you have been provided feedback, choose your action based on it. Only redo the steps deemed necessary by the feedback. " +
                "NB: The setup script must be written and completed before the final implementation."
            )

            self.implementation_result = None

            while not self.implementation_result:

                run_result = await self._run_agent(
                    swe_prompt,
                    output_type=[
                        PlanningOutput,
                        # TODO: Add setup, will need to spin up extra container in this case
                        # submit_setup_output,
                        ConfigOutput,
                        submit_implementation_output
                    ],
                    deps=self.deps
                )

                if isinstance(run_result.output, PlanningOutput):
                    self.plan_result = run_result
                    if self.log:
                        await self._log_message("Plan complete", "result")
                        await self._log_message(f"Plan result: {self.plan_result}", "result", write_to_db=True)

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
                        await self._log_message("Config complete", "result")
                        await self._log_message(f"Config result: {self.config_result}", "result", write_to_db=True)

                elif isinstance(run_result.output, ImplementationOutputFull):
                    self.implementation_result = run_result

                    # Replace "functions_tmp" with "functions" in the script
                    script = self.implementation_result.output.script
                    self.implementation_result.output.script = script.replace(
                        "functions_tmp", "functions")

                    if self.log:
                        await self._log_message(
                            "Implementation complete", "result")
                        await self._log_message(f"Implementation result: {self.implementation_result}", "result", write_to_db=True)

                else:
                    raise RuntimeError(
                        f"Unrecognized agent return type: {run_result.output}")

                swe_prompt = "Choose your action"

            await self._complete_agent_run("SWE agent run completed")

            return SWEAgentOutput(
                plan=self.plan_result.output if self.plan_result else None,
                setup=self.setup_result.output if self.setup_result else None,
                config=self.config_result.output if self.config_result else None,
                implementation=self.implementation_result.output,
            )

        except Exception as e:
            self.delete_temporary_scripts()
            await self._fail_agent_run(f"Error running SWE agent: {e}")
            if self.container and self.new_container_created:
                self.container.stop()
                self.container.remove()
                self.new_container_created = False
            raise e

    def delete_temporary_scripts(self) -> None:
        for script_name in list(self.deps.current_scripts.keys()):
            file_manager.delete_function_script(
                script_name, 0, is_temporary=True)
            self.deps.current_scripts.pop(script_name)
            if script_name in self.deps.input_scripts:
                self.deps.input_scripts.pop(script_name)

    def _prepare_deps(self) -> SWEAgentDeps:

        deps = SWEAgentDeps(
            cwd=str(self.container_cwd),
            container_name=self.container_name,
            test_code_to_append_to_implementation=None,
            structure_ids_to_inject=self.structure_ids_to_inject,
            inject_synthetic_data_descriptions=self.inject_synthetic_data_descriptions,
            input_scripts=self.scripts_to_inject,
            log=self.log,
            modified_scripts=set()
        )

        if self.scripts_to_inject:
            assert len(self.scripts_to_inject) == len(set(
                [function_def.script_name for function_def in self.scripts_to_inject])), "All function names must be unique"

            deps.input_scripts = {}
            deps.current_scripts = {}
            for function_def in self.scripts_to_inject:
                with open(function_def.script_path, "r") as f:
                    script_content = f.read()

                deps.input_scripts[function_def.script_name] = script_content
                deps.current_scripts[function_def.script_name] = script_content
                file_manager.save_function_script(
                    function_def.script_name, script_content, 0, is_temporary=True)

        return deps

    async def _setup_container(self) -> None:

        if self.container is not None:
            return

        if self.create_new_container_on_start:
            if self.log:
                await self._log_message("Setting up Docker container for SWE agent...", "tool_call")

            # Is now sync, blocking the main thread, TODO: Make async
            self.container = self.docker_client.containers.create(
                self.base_image,
                name=self.container_name
            )

            self.container.start()
            self.new_container_created = True

            if self.log:
                await self._log_message("Docker container started successfully", "result")

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
                await self._log_message(f"Error creating directory: {err}", "result")
            raise RuntimeError(f"Error creating directory: {err}")

    async def _install_python_version(self, python_version: str) -> None:
        if self.log:
            await self._log_message(f"Installing Python version: {python_version}", "tool_call")

        check_output, _ = await run_shell_code_in_container(
            f"pyenv versions | grep {python_version}",
            container_name=self.container_name
        )

        if not check_output.strip():
            out, err = await run_shell_code_in_container(
                f"pyenv install {python_version}",
                container_name=self.container_name,
            )

            if err:
                if self.log:
                    await self._log_message(f"Error installing Python version: {err}", "result")
                raise RuntimeError(f"Error installing python version: {err}")

        out, err = await run_shell_code_in_container(
            f"pyenv global {python_version}",
            container_name=self.container_name
        )

        if err:
            if self.log:
                await self._log_message(f"Error setting global Python version: {err}", "result")
            raise RuntimeError(f"Error setting global python version: {err}")

        if self.log:
            await self._log_message(f"Python {python_version} installed and set as global version", "result")

        return out

    async def _run_setup_script(self, setup_script: str) -> None:
        if self.log:
            await self._log_message("Running setup script...", "tool_call")

        out, err = await run_shell_code_in_container(
            setup_script,
            container_name=self.container_name,
            cwd=str(self.container_cwd)
        )

        if err:
            if self.log:
                await self._log_message(f"Error running setup script: {err}", "result")
            raise RuntimeError(f"Error running setup script: {err}")

        if self.log:
            await self._log_message("Setup script run successfully", "result")

        return out

    async def _save_results(self, results: SWEAgentOutput) -> None:
        pass
