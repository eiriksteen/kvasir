import uuid
import docker
from pathlib import Path
from typing import Union, List, Literal, Optional, Tuple
from datetime import datetime, timezone
from pydantic_ai import Agent
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    ModelMessage
)
from synesis_api.utils import (
    run_shell_code_in_container,
    create_file_in_container_with_content,
    parse_github_url,
    run_python_code_in_container
)
from synesis_api.worker import broker
from synesis_api.base_schema import BaseSchema
from synesis_api.redis import get_redis
from synesis_api.agents.model_integration.setup_agent.agent import (
    SetupAgentOutputWithScript,
    setup_agent
)
from synesis_api.agents.model_integration.implementation_agent.agent import (
    ModelAnalysisOutput,
    ImplementationPlanningOutput,
    TrainingOutputWithScript,
    InferenceOutputWithScript,
    implementation_agent
)
from synesis_api.agents.model_integration.deps import ModelIntegrationDeps
from synesis_api.modules.runs.schema import RunInDB
from synesis_api.modules.runs.service import update_run_status, get_run, create_run_message_pydantic, create_model_integration_run_result
from synesis_api.modules.automation.service import insert_model
from synesis_api.agents.model_integration.utils import (
    save_stage_output_to_cache,
    get_stage_output_from_cache,
    get_message_history_from_cache
)
from synesis_api.agents.model_integration.input_structures import get_input_structure, get_config_definition_code
from synesis_api.agents.model_integration.output_structures import get_output_structure
from synesis_api.modules.raw_data_storage.service import save_script_to_local_storage


class ModelIntegrationOutput(BaseSchema):
    setup_output: SetupAgentOutputWithScript
    model_analysis_output: ModelAnalysisOutput
    planning_outputs: List[ImplementationPlanningOutput]
    training_outputs: List[TrainingOutputWithScript]
    inference_outputs: List[InferenceOutputWithScript]


class ModelIntegrationRunner:

    def __init__(
            self,
            user_id: str,
            model_id: str,
            run_id: uuid.UUID,
            conversation_id: uuid.UUID,
            source: Literal["github", "pip"] = "github"):

        self.setup_agent = setup_agent
        self.implementation_agent = implementation_agent
        self.user_id = user_id
        self.model_id = model_id
        self.run_id = run_id
        self.conversation_id = conversation_id
        self.source = source
        self.base_image = "model-integration-image"
        self.docker_client = docker.from_env()
        self.run = None
        self.container = None
        self.container_name = f"model-integration-{self.run_id}"
        self.container_cwd = None
        self.redis_stream = get_redis()
        self.stage: Literal["setup",
                            "model_analysis",
                            "implementation_planning",
                            "training",
                            "inference"] = "setup"
        self.current_task: Optional[Literal["classification",
                                            "regression",
                                            "segmentation",
                                            "forecasting"]] = None

        if source == "github":
            self.github_info = parse_github_url(model_id)
        elif source == "pip":
            self.github_info = None

    async def get_run(self) -> RunInDB:
        """Get the run metadata"""
        if self.run is None:
            self.run = await get_run(self.job_id)
        return self.run

    async def _update_job_status(self, status: Literal["running", "completed", "failed"]) -> None:
        self.run = await update_run_status(self.run.id, status)

    def _set_stage(self, stage: Literal["setup", "implementation"],
                   current_task: Optional[Literal["classification", "regression", "segmentation", "forecasting"]] = None) -> None:
        """Set the current stage and optionally the current task"""
        self.stage = stage
        self.current_task = current_task

    async def _log_message_to_redis(self, content: str, message_type: Literal["tool_call", "result", "error", "chat"]):
        """Log a message to Redis stream"""
        message = {
            "id": str(uuid.uuid4()),
            "role": "agent",
            "conversation_id": str(self.conversation_id),
            "run_id": str(self.run_id),
            "type": message_type,
            "content": content,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.redis_stream.xadd(str(self.run_id), message)

    async def _setup_container(self) -> None:
        assert self.stage == "setup", f"setup_container can only be called during setup stage, current stage: {self.stage}"

        if self.container is not None:
            await self._log_message_to_redis("Container already exists, skipping setup")
            return

        await self._log_message_to_redis("Setting up Docker container for model integration...")

        # Is now sync, blocking the main thread, TODO: Make async
        self.container = self.docker_client.containers.create(
            self.base_image,
            name=self.container_name,
        )
        self.container.start()
        await self._log_message_to_redis("Docker container started successfully", "result")

    async def _github_repo_setup(self) -> Path:
        assert self.stage == "setup", f"github_repo_setup can only be called during setup stage, current stage: {self.stage}"
        await self._log_message_to_redis(f"Cloning GitHub repository: {self.model_id}")

        assert self.source == "github", "Can only clone from github for now"

        _, err = await run_shell_code_in_container(
            f"git clone {self.model_id}.git",
            container_name=self.container_name
        )

        if err:
            await self._log_message_to_redis(f"Error cloning repository: {err}", "result")
            raise RuntimeError(f"Error cloning repo: {err}")

        cwd = Path("/app") / self.github_info["repo"]
        await self._log_message_to_redis(f"Repository cloned successfully to {cwd}", "result")

        return cwd

    async def _pip_package_setup(self) -> Path:
        assert self.stage == "setup", f"pip_package_setup can only be called during setup stage, current stage: {self.stage}"
        await self._log_message_to_redis(f"Setting up pip package: {self.model_id}")

        cwd = Path("/app") / f"{self.model_id}-integration"

        _, err = await run_shell_code_in_container(
            f"mkdir -p {str(cwd)}",
            container_name=self.container_name
        )

        if err:
            await self._log_message_to_redis(f"Error creating directory: {err}", "result")
            raise RuntimeError(f"Error creating directory: {err}")

        await self._log_message_to_redis(f"Directory created successfully at {cwd}", "result")
        return cwd

    async def _install_python_version(self, python_version: str) -> None:
        assert self.stage == "setup", f"install_python_version can only be called during setup stage, current stage: {self.stage}"
        await self._log_message_to_redis(f"Installing Python version: {python_version}")

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
                await self._log_message_to_redis(f"Error installing Python version: {err}", "result")
                raise RuntimeError(f"Error installing python version: {err}")

        out, err = await run_shell_code_in_container(
            f"pyenv global {python_version}",
            container_name=self.container_name
        )

        if err:
            await self._log_message_to_redis(f"Error setting global Python version: {err}", "result")
            raise RuntimeError(f"Error setting global python version: {err}")

        await self._log_message_to_redis(f"Python {python_version} installed and set as global version", "result")
        return out

    async def _run_setup_script(self, setup_script: str) -> None:
        assert self.stage == "setup", f"run_setup_script can only be called during setup stage, current stage: {self.stage}"
        await self._log_message_to_redis("Running setup script...")

        out, err = await run_shell_code_in_container(
            setup_script,
            container_name=self.container_name,
            cwd=self.container_cwd
        )

        if err:
            await self._log_message_to_redis(f"Error running setup script: {err}", "result")
            raise RuntimeError(f"Error running setup script: {err}")

        await self._log_message_to_redis("Setup script run successfully", "result")
        return out

    async def _save_file_to_container(self, file_path: str, file_content: str) -> None:
        await create_file_in_container_with_content(
            file_path,
            file_content,
            container_name=self.container_name
        )

    async def _run_training_script(self, training_script: str) -> None:
        out, err = await run_python_code_in_container(
            training_script,
            container_name=self.container_name,
            cwd=self.container_cwd
        )

        if err:
            await self._log_message_to_redis(f"Error running training script: {err}", "result")
            raise RuntimeError(f"Error running training script: {err}")

        await self._log_message_to_redis("Training script run successfully", "result")
        return out

    async def _run_agent(
            self,
            agent: Agent[ModelIntegrationDeps],
            user_prompt: str,
            output_type: Union[SetupAgentOutputWithScript,
                               ModelAnalysisOutput,
                               ImplementationPlanningOutput,
                               TrainingOutputWithScript,
                               InferenceOutputWithScript] = None,
            deps: ModelIntegrationDeps = None,
            message_history: list[ModelMessage] = None
    ) -> AgentRunResult[Union[SetupAgentOutputWithScript, ModelAnalysisOutput, ImplementationPlanningOutput, TrainingOutputWithScript, InferenceOutputWithScript]]:

        async with agent.iter(
                user_prompt=user_prompt,
                deps=deps,
                message_history=message_history,
                output_type=output_type) as run:
            async for node in run:
                if Agent.is_call_tools_node(node):
                    async with node.stream(run.ctx) as handle_stream:
                        async for event in handle_stream:
                            if isinstance(event, FunctionToolCallEvent):
                                message = f'[Tools] The LLM calls tool={event.part.tool_name!r} with args={event.part.args}'
                                await self._log_message_to_redis(message, "tool_call")

        return run.result

    async def _run_setup(self) -> SetupAgentOutputWithScript:
        await self.get_run()
        await self._update_job_status("running")
        await self._setup_container()
        self._set_stage("setup")

        if self.source == "github":
            self.container_cwd = await self._github_repo_setup()
        elif self.source == "pip":
            self.container_cwd = await self._pip_package_setup()
        else:
            raise ValueError(f"Invalid source: {self.source}")

        # Get output (from cache or run agent)
        cached_setup = await get_stage_output_from_cache(self.model_id, self.source, "setup")
        if cached_setup:
            await self._log_message_to_redis("Found cached setup output, using cached result", "result")
            setup_output = SetupAgentOutputWithScript(**cached_setup["output"])
        else:
            await self._log_message_to_redis("Starting model setup analysis...")
            setup_run = await self._run_agent(
                self.setup_agent,
                user_prompt="We are now in the setup stage, begin!",
                deps=ModelIntegrationDeps(
                    model_id=self.model_id,
                    container_name=self.container_name,
                    cwd=str(self.container_cwd),
                    source=self.source,
                    integration_id=self.run_id,
                    stage="setup"
                )
            )
            setup_output = setup_run.output

            await create_run_message_pydantic(
                run_id=self.run_id,
                messages=setup_run.all_messages_json()
            )

            # Cache the setup output
            await save_stage_output_to_cache(
                self.model_id,
                self.source,
                "setup",
                setup_output.model_dump()
            )

        await self._install_python_version(setup_output.python_version)
        await self._run_setup_script(setup_output.script)

        await self._log_message_to_redis("Model setup completed successfully", "result")
        return setup_output

    async def _run_model_analysis(self, python_version: str) -> Tuple[ModelAnalysisOutput, list[ModelMessage]]:
        self._set_stage("model_analysis")

        # Get output (from cache or run agent)
        cached_analysis = await get_stage_output_from_cache(self.model_id, self.source, "model_analysis")
        if cached_analysis:
            await self._log_message_to_redis("Found cached model analysis output, using cached result", "result")
            analysis_output = ModelAnalysisOutput(**cached_analysis["output"])
            message_history = await get_message_history_from_cache(
                self.model_id, self.source)
            if message_history is None:
                raise RuntimeError(
                    "Message history not found in cache, but output was found")
        else:
            await self._log_message_to_redis("Starting model analysis...")
            model_analysis_run = await self._run_agent(
                self.implementation_agent,
                user_prompt=("We are now in the model analysis stage"
                             f"The model id is {self.model_id} and the source is {self.source}"
                             f"Your cwd is {self.container_cwd}"
                             f"The installed python version is {python_version}"
                             f"[BASE CONFIG DEFINITION]\n\n{get_config_definition_code()}\n\n"
                             "Start the analysis!"),
                deps=ModelIntegrationDeps(
                    model_id=self.model_id,
                    container_name=self.container_name,
                    cwd=str(self.container_cwd),
                    source=self.source,
                    integration_id=self.run_id,
                    stage="model_analysis"
                )
            )
            analysis_output = model_analysis_run.output
            message_history = model_analysis_run.all_messages()

            await create_run_message_pydantic(
                run_id=self.run_id,
                messages=model_analysis_run.all_messages_json()
            )

            # Cache the model analysis output
            await save_stage_output_to_cache(
                self.model_id,
                self.source,
                "model_analysis",
                analysis_output.model_dump(),
                model_analysis_run.all_messages_json()
            )

        # Run necessary functions regardless of cache
        await self._save_file_to_container(
            str(self.container_cwd / "config.py"),
            analysis_output.config_code
        )

        await self._log_message_to_redis("Model analysis completed successfully", "result")
        return analysis_output, message_history

    async def _run_implementation(
            self,
            model_analysis_output: ModelAnalysisOutput,
            message_history: list[ModelMessage]
    ) -> Tuple[List[ImplementationPlanningOutput], List[TrainingOutputWithScript], List[InferenceOutputWithScript]]:
        planning_outputs = []
        training_outputs = []
        inference_outputs = []

        for task in model_analysis_output.supported_tasks:
            # Get planning output (from cache or run agent)
            cached_planning = await get_stage_output_from_cache(self.model_id, self.source, f"planning_{task}")
            if cached_planning:
                await self._log_message_to_redis(f"Found cached planning output for task: {task}, using cached result", "result")
                planning_output = ImplementationPlanningOutput(
                    **cached_planning["output"])
            else:
                self._set_stage("implementation_planning", task)
                await self._log_message_to_redis(f"Starting implementation for task: {task}")
                planning_run = await self._run_agent(
                    self.implementation_agent,
                    user_prompt=(
                        f"We are now in the implementation planning stage. The current task is {task}"
                        f"[INPUT STRUCTURE]\n\n{get_input_structure(model_analysis_output.modality)}\n\n"
                        f"[OUTPUT STRUCTURE]\n\n{get_output_structure(model_analysis_output.modality, task)}\n\n"
                        "Start the planning!"
                    ),
                    deps=ModelIntegrationDeps(
                        current_task=task,
                        modality=model_analysis_output.modality,
                        container_name=self.container_name,
                        cwd=str(self.container_cwd),
                        model_id=self.model_id,
                        source=self.source,
                        integration_id=self.run_id,
                        stage="implementation_planning"
                    ),
                    message_history=message_history
                )
                planning_output = planning_run.output
                message_history = planning_run.all_messages()

                await create_run_message_pydantic(
                    run_id=self.run_id,
                    messages=planning_run.new_messages_json()
                )

                # Cache the planning output
                await save_stage_output_to_cache(
                    self.model_id,
                    self.source,
                    f"planning_{task}",
                    planning_output.model_dump(),
                    planning_run.all_messages_json()
                )

            planning_outputs.append(planning_output)

            # Get training output (from cache or run agent)
            cached_training = await get_stage_output_from_cache(self.model_id, self.source, f"training_{task}")
            if cached_training:
                await self._log_message_to_redis(f"Found cached training output for task: {task}, using cached result", "result")
                training_output = TrainingOutputWithScript(
                    **cached_training["output"])
            else:
                self._set_stage("training", task)
                await self._log_message_to_redis(f"Starting training implementation for task: {task}")
                training_run = await self._run_agent(
                    self.implementation_agent,
                    user_prompt="We are now in the training stage, begin!",
                    deps=ModelIntegrationDeps(
                        current_task=task,
                        modality=model_analysis_output.modality,
                        container_name=self.container_name,
                        cwd=str(self.container_cwd),
                        model_id=self.model_id,
                        source=self.source,
                        integration_id=self.job_id,
                        stage="training"
                    ),
                    message_history=message_history
                )
                training_output = training_run.output
                message_history = training_run.all_messages()

                await create_run_message_pydantic(
                    run_id=self.run_id,
                    messages=training_run.new_messages_json()
                )

                # Cache the training output
                await save_stage_output_to_cache(
                    self.model_id,
                    self.source,
                    f"training_{task}",
                    training_output.model_dump(),
                    training_run.all_messages_json()
                )

            await self._run_training_script(training_output.script)

            training_outputs.append(training_output)

            # Save training script to container
            await self._save_file_to_container(
                str(self.container_cwd / f"training_{task}.py"),
                training_output.script
            )

            await self._log_message_to_redis(f"Training script successfully implemented for task: {task}", "result")

            # Get inference output (from cache or run agent)
            cached_inference = await get_stage_output_from_cache(self.model_id, self.source, f"inference_{task}")
            if cached_inference:
                await self._log_message_to_redis(f"Found cached inference output for task: {task}, using cached result", "result")
                inference_output = InferenceOutputWithScript(
                    **cached_inference["output"])
            else:
                self._set_stage("inference", task)
                await self._log_message_to_redis(f"Starting inference implementation for task: {task}")
                inference_run = await self._run_agent(
                    self.implementation_agent,
                    user_prompt=(
                        f"We are now in the inference stage.\n\n"
                        f"[TRAINING SCRIPT]\n\n{training_output.script}\n\n"
                        "Start writing the inference script!"
                    ),
                    deps=ModelIntegrationDeps(
                        current_task=task,
                        modality=model_analysis_output.modality,
                        container_name=self.container_name,
                        cwd=str(self.container_cwd),
                        model_id=self.model_id,
                        source=self.source,
                        integration_id=self.job_id,
                        stage="inference"
                    ),
                    message_history=message_history
                )
                inference_output = inference_run.output
                message_history = inference_run.all_messages()

                await create_run_message_pydantic(
                    run_id=self.run_id,
                    messages=inference_run.new_messages_json()
                )

                # Cache the inference output
                await save_stage_output_to_cache(
                    self.model_id,
                    self.source,
                    f"inference_{task}",
                    inference_output.model_dump(),
                    inference_run.all_messages_json()
                )

            inference_outputs.append(inference_output)

            await self._log_message_to_redis(f"Inference script successfully implemented for task: {task}", "result")

            # Save inference script to container
            await self._save_file_to_container(
                str(self.container_cwd / f"inference_{task}.py"),
                inference_output.script
            )

        return planning_outputs, training_outputs, inference_outputs

    async def _save_results(self,
                            setup_output: SetupAgentOutputWithScript,
                            model_analysis_output: ModelAnalysisOutput,
                            planning_outputs: List[ImplementationPlanningOutput],
                            training_outputs: List[TrainingOutputWithScript],
                            inference_outputs: List[InferenceOutputWithScript]) -> None:

        # Save setup script to local machine
        setup_script_path = save_script_to_local_storage(
            self.user_id,
            self.job_id,
            setup_output.script,
            "setup.sh",
            "automation"
        )

        # Save files to local system
        inference_save_paths, training_save_paths = [], []

        for i, task in enumerate(model_analysis_output.supported_tasks):

            inference_script_path = save_script_to_local_storage(
                self.user_id,
                self.job_id,
                inference_outputs[i].script,
                f"inference_{task}.py",
                "automation"
            )

            training_script_path = save_script_to_local_storage(
                self.user_id,
                self.job_id,
                training_outputs[i].script,
                f"training_{task}.py",
                "automation"
            )

            inference_save_paths.append(str(inference_script_path))
            training_save_paths.append(str(training_script_path))

        # Save config file
        config_script_path = save_script_to_local_storage(
            self.user_id,
            self.job_id,
            model_analysis_output.config_code,
            "config.py",
            "automation"
        )

        # Save to database
        await self._log_message_to_redis("Saving model to database...")
        model_id = uuid.uuid4()

        await insert_model(
            name=model_analysis_output.model_name,
            description=model_analysis_output.model_description,
            owner_id=self.user_id,
            public=False,
            modality_name=model_analysis_output.modality,
            source_name=self.source,
            programming_language_name="python",
            programming_language_version_name=setup_output.python_version,
            setup_script_path=str(setup_script_path),
            config_script_path=str(config_script_path),
            input_description=model_analysis_output.model_input_description,
            output_description=model_analysis_output.model_output_description,
            config_parameters=model_analysis_output.config_parameters,
            tasks=model_analysis_output.supported_tasks,
            inference_script_paths=inference_save_paths,
            training_script_paths=training_save_paths,
            model_id=model_id
        )

        # Save Redis stream messages to database
        streamed_nodes = await self.redis_stream.xread({str(self.job_id): 0}, count=None)
        integration_messages = []

        for item in streamed_nodes[0][1]:
            if item[1]["type"] in ["tool_call", "result"]:
                message = item[1].copy()
                message["created_at"] = datetime.fromisoformat(
                    message["created_at"]).replace(tzinfo=timezone.utc)

                integration_messages.append(message)

        await self._update_job_status("completed")
        await self._log_message_to_redis(f"Model integration completed successfully! Model ID: {model_id}", "result")
        await create_model_integration_run_result(run_id=self.run_id, model_id=model_id)

        return ModelIntegrationOutput(
            setup_output=setup_output,
            model_analysis_output=model_analysis_output,
            planning_outputs=planning_outputs,
            training_outputs=training_outputs,
            inference_outputs=inference_outputs
        )

    async def __call__(self) -> ModelIntegrationOutput:

        try:
            setup_output = await self._run_setup()

            model_analysis_output, message_history = await self._run_model_analysis(setup_output.python_version)

            planning_outputs, training_outputs, inference_outputs = await self._run_implementation(
                model_analysis_output,
                message_history
            )

            final_output = await self._save_results(setup_output, model_analysis_output, planning_outputs, training_outputs, inference_outputs)

            self.container.stop()
            self.container.remove()

            return final_output

        except Exception as e:
            await self._log_message_to_redis(f"Model integration failed: {str(e)}", "result")
            await self._update_job_status("failed")
            if self.container:
                self.container.stop()
                self.container.remove()
            raise e


@broker.task(retry_on_error=False)
async def run_model_integration_task(
        user_id: str,
        model_id: str,
        run_id: uuid.UUID,
        source: Literal["github", "pip"] = "github") -> ModelIntegrationOutput:

    runner = ModelIntegrationRunner(user_id, model_id, run_id, source)
    result = await runner()
    return result
