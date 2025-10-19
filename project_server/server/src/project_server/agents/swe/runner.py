import uuid
import docker
from typing import Optional, List, Callable
from pathlib import Path

from project_server.agents.swe.agent import swe_agent
from project_server.agents.swe.output import (
    SWEAgentOutput,
    ImplementationOutputFull,
    # SetupAgentOutputWithScript,
    # submit_setup_output,
    submit_implementation_output
)
from project_server.agents.swe.deps import SWEAgentDeps, FunctionInjected, ModelInjected
from project_server.utils.code_utils import run_shell_code_in_container, add_line_numbers_to_script
from project_server.agents.runner_base import RunnerBase, MessageForLog
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
            log: bool = False,
            structure_ids_to_inject: Optional[List[str]] = None,
            inject_synthetic_data_descriptions: bool = False,
            functions_to_inject: Optional[List[FunctionInjected]] = None,
            models_to_inject: Optional[List[ModelInjected]] = None,
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

        self.setup_result = None
        self.implementation_result = None
        self.container = None
        self.log = log
        self.container_name = "project-sandbox"
        self.container_cwd = Path("/app")
        self.functions_to_inject = functions_to_inject
        self.models_to_inject = models_to_inject
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
        self.deps = SWEAgentDeps(
            cwd=str(self.container_cwd),
            container_name=self.container_name,
            test_code_to_append_to_implementation=None,
            structure_ids_to_inject=self.structure_ids_to_inject,
            inject_synthetic_data_descriptions=self.inject_synthetic_data_descriptions,
            client=self.project_client,
            log_code=self._log_code,
        )

        self._inject_functions_and_models()

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
                "Now choose your action. Write the setup script or the final implementation. " +
                "In case you have been provided feedback, choose your action based on it. Only redo the steps deemed necessary by the feedback. " +
                "NB: The setup script must be written and completed before the final implementation." +
                ""
            )

            self.implementation_result = None

            while not self.implementation_result:

                run_result = await self._run_agent(
                    swe_prompt,
                    output_type=[
                        # TODO: Add setup, will need to spin up extra container in this case
                        # submit_setup_output,
                        submit_implementation_output
                    ],
                    deps=self.deps
                )

                # TODO: 'elif isinstance(run_result.output, SetupAgentOutputWithScript):' ...

                if isinstance(run_result.output, ImplementationOutputFull):
                    self.implementation_result = run_result.output

                    if self.log:
                        await self._log_message(MessageForLog(
                            content=f"Implementation result: {self.implementation_result.model_dump_json()}",
                            type="result",
                            write_to_db=1
                        ))

                else:
                    raise RuntimeError(
                        f"Unrecognized agent return type: {run_result.output}")

                swe_prompt = "Choose your action"

            await self._complete_agent_run("SWE agent run completed")

            return SWEAgentOutput(
                setup=self.setup_result if self.setup_result else None,
                implementation=self.implementation_result,
            )

        except Exception as e:
            self.delete_temporary_scripts()
            await self._fail_agent_run(f"Error running SWE agent: {e}")
            if self.container and self.new_container_created:
                self.container.stop()
                self.container.remove()
                self.new_container_created = False
            raise e

    def get_final_output(self) -> SWEAgentOutput:
        self.delete_temporary_scripts()
        implementation_output = self.implementation_result
        implementation_output.main_script.script = file_manager.clean_temporary_script(
            implementation_output.main_script.script)

        for new_script in implementation_output.new_scripts:
            new_script.script = file_manager.clean_temporary_script(
                new_script.script)

        for modified_script in implementation_output.modified_scripts:
            modified_script.original_script = file_manager.clean_temporary_script(
                modified_script.original_script)
            modified_script.new_script = file_manager.clean_temporary_script(
                modified_script.new_script)

        self.implementation_result = implementation_output

        return SWEAgentOutput(
            implementation=implementation_output,
            setup=self.setup_result if self.setup_result else None,
        )

    def delete_temporary_scripts(self) -> None:
        # Delete current scripts
        for filename in list(self.deps.current_scripts.keys()):
            file_manager.delete_temporary_script(filename)
        # Delete old scripts
        for filename in list(self.deps.modified_scripts_old_to_new_name.keys()):
            file_manager.delete_temporary_script(filename)

    def _inject_functions_and_models(self) -> SWEAgentDeps:

        current_scripts = {}

        if self.functions_to_inject:
            assert len(self.functions_to_inject) == len(set(
                [function_def.filename for function_def in self.functions_to_inject])), "All function names must be unique"

            functions_injected = []
            for function_def in self.functions_to_inject:
                with open(function_def.script_path, "r") as f:
                    script_content = f.read()

                function_storage = file_manager.save_script(
                    function_def.filename, script_content, "function", add_uuid=False, temporary=True)

                fn = FunctionInjected(
                    filename=function_storage.filename,
                    script_path=function_storage.script_path,
                    docstring=function_def.docstring,
                    module_path=function_storage.module_path
                )

                functions_injected.append(fn)
                current_scripts[function_storage.filename] = script_content

            self.deps.functions_injected = functions_injected

        if self.models_to_inject:
            assert len(self.models_to_inject) == len(set(
                [model_def.filename for model_def in self.models_to_inject])), "All model names must be unique"

            models_injected = []
            for model_def in self.models_to_inject:
                with open(model_def.script_path, "r") as f:
                    script_content = f.read()

                model_storage = file_manager.save_script(
                    model_def.filename, script_content, "model", add_uuid=False, temporary=True)

                mdl = ModelInjected(
                    filename=model_storage.filename,
                    script_path=model_storage.script_path,
                    module_path=model_storage.module_path,
                    model_class_docstring=model_def.model_class_docstring,
                    training_function_docstring=model_def.training_function_docstring,
                    inference_function_docstring=model_def.inference_function_docstring
                )

                models_injected.append(mdl)
                current_scripts[model_storage.filename] = script_content

            self.deps.models_injected = models_injected

        self.deps.current_scripts = current_scripts

    async def _setup_container(self) -> None:

        if self.container is not None:
            return

        if self.create_new_container_on_start:
            if self.log:
                await self._log_message(MessageForLog(
                    content="Setting up Docker container for SWE agent...",
                    type="tool_call",
                    write_to_db=1
                ))

            # Is now sync, blocking the main thread, TODO: Make async
            self.container = self.docker_client.containers.create(
                self.base_image,
                name=self.container_name
            )

            self.container.start()
            self.new_container_created = True

            if self.log:
                await self._log_message(MessageForLog(
                    content="Docker container started successfully",
                    type="result",
                    write_to_db=1
                ))

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
                await self._log_message(MessageForLog(
                    content=f"Error creating directory: {err}",
                    type="result",
                    write_to_db=1
                ))
            raise RuntimeError(f"Error creating directory: {err}")

    async def _install_python_version(self, python_version: str) -> None:
        if self.log:
            await self._log_message(MessageForLog(
                content=f"Installing Python version: {python_version}",
                type="tool_call",
                write_to_db=1
            ))

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
                    await self._log_message(MessageForLog(
                        content=f"Error installing Python version: {err}",
                        type="result",
                        write_to_db=1
                    ))
                raise RuntimeError(f"Error installing python version: {err}")

        out, err = await run_shell_code_in_container(
            f"pyenv global {python_version}",
            container_name=self.container_name
        )

        if err:
            if self.log:
                await self._log_message(MessageForLog(
                    content=f"Error setting global Python version: {err}",
                    type="result",
                    write_to_db=1
                ))
            raise RuntimeError(f"Error setting global python version: {err}")

        if self.log:
            await self._log_message(MessageForLog(
                content=f"Python {python_version} installed and set as global version",
                type="result",
                write_to_db=1
            ))

        return out

    async def _run_setup_script(self, setup_script: str) -> None:
        if self.log:
            await self._log_message(MessageForLog(
                content="Running setup script...",
                type="tool_call",
                write_to_db=1
            ))

        out, err = await run_shell_code_in_container(
            setup_script,
            container_name=self.container_name,
            cwd=str(self.container_cwd)
        )

        if err:
            if self.log:
                await self._log_message(MessageForLog(
                    content=f"Error running setup script: {err}",
                    type="result",
                    write_to_db=1
                ))
            raise RuntimeError(f"Error running setup script: {err}")

        if self.log:
            await self._log_message(MessageForLog(
                content="Setup script run successfully",
                type="result",
                write_to_db=1
            ))

        return out

    async def _save_results(self, results: SWEAgentOutput) -> None:
        pass
