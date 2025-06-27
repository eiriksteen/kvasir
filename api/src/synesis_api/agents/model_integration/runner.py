import uuid
import json
import docker
from pathlib import Path
from typing import Union, List, Literal, Optional
from datetime import datetime, timezone
from pydantic_ai import Agent
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ModelMessage
)
from synesis_api.utils import (
    run_shell_code_in_container,
    create_file_in_container_with_content,
    parse_github_url
)
from synesis_api.worker import broker, logger
from synesis_api.base_schema import BaseSchema
from synesis_api.redis import get_redis
from synesis_api.agents.model_integration.setup_agent.agent import SetupDeps, SetupAgentOutputWithScript, setup_agent
from synesis_api.agents.model_integration.model_analysis_agent.agent import ModelAnalysisDeps, ModelAnalysisAgentOutput, model_analysis_agent
from synesis_api.agents.model_integration.planner_agent.agent import PlannerDeps, planning_agent
from synesis_api.agents.model_integration.training_agent.agent import TrainingDeps, TrainingAgentOutputWithScript, training_agent
from synesis_api.agents.model_integration.inference_agent.agent import InferenceDeps, InferenceAgentOutputWithScript, inference_agent
from synesis_api.modules.jobs.schema import JobMetadata
from synesis_api.modules.jobs.service import update_job_status, get_job_metadata
from synesis_api.modules.automation.service import insert_model
from synesis_api.modules.model_integration.service import (
    create_model_integration_result,
    create_model_integration_messages_pydantic,
    create_model_integration_messages
)


class ModelIntegrationOutput(BaseSchema):
    setup_output: SetupAgentOutputWithScript
    model_analysis_output: ModelAnalysisAgentOutput
    planner_outputs: List[str]
    training_outputs: List[TrainingAgentOutputWithScript]
    inference_outputs: List[InferenceAgentOutputWithScript]


class ModelIntegrationRunner:

    def __init__(
            self,
            user_id: str,
            model_id: str,
            job_id: uuid.UUID,
            source: Literal["github", "pip"] = "github"):

        self.setup_agent = setup_agent
        self.model_analysis_agent = model_analysis_agent
        self.planner_agent = planning_agent
        self.training_agent = training_agent
        self.inference_agent = inference_agent
        self.user_id = user_id
        self.model_id = model_id
        self.job_id = job_id
        self.source = source
        self.base_image = "model-integration-image"
        self.docker_client = docker.from_env()
        self.job = None
        self.container = None
        self.container_name = f"model-integration-{self.job_id}"
        self.redis_stream = get_redis()
        self.stage: Literal["setup", "analysis",
                            "planning", "training", "inference"] = "setup"
        self.current_task: Optional[Literal["classification",
                                            "regression", "segmentation", "forecasting"]] = None

        if source == "github":
            self.github_info = parse_github_url(model_id)
        elif source == "pip":
            self.github_info = None

    async def get_job(self) -> JobMetadata:
        """Get the job metadata"""
        if self.job is None:
            self.job = await get_job_metadata(self.job_id)
        return self.job

    async def _update_job_status(self, status: Literal["running", "completed", "failed"]) -> None:
        self.job = await update_job_status(self.job.id, status)

    def _set_stage(self, stage: Literal["setup", "analysis", "planning", "training", "inference"],
                   current_task: Optional[Literal["classification", "regression", "segmentation", "forecasting"]] = None) -> None:
        """Set the current stage and optionally the current task"""
        self.stage = stage
        self.current_task = current_task

    async def _log_message(self, content: str, message_type: str = "tool_call"):
        """Log a message to Redis stream"""
        message = {
            "id": str(uuid.uuid4()),
            "type": message_type,
            "role": "assistant",
            "content": content,
            "stage": self.stage,
            "current_task": "null" if self.current_task is None else self.current_task,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.redis_stream.xadd(str(self.job_id), message)

    async def _setup_container(self) -> None:
        assert self.stage == "setup", f"setup_container can only be called during setup stage, current stage: {self.stage}"

        if self.container is not None:
            await self._log_message("Container already exists, skipping setup")
            return

        await self._log_message("Setting up Docker container for model integration...")

        # Is now sync, blocking the main thread, TODO: Make async
        self.container = self.docker_client.containers.create(
            self.base_image,
            name=self.container_name,
        )
        self.container.start()
        await self._log_message("Docker container started successfully", "result")

    async def _github_repo_setup(self) -> Path:
        assert self.stage == "setup", f"github_repo_setup can only be called during setup stage, current stage: {self.stage}"
        await self._log_message(f"Cloning GitHub repository: {self.model_id}")

        assert self.source == "github", "Can only clone from github for now"

        _, err = await run_shell_code_in_container(
            f"git clone {self.model_id}.git",
            container_name=self.container_name
        )

        if err:
            await self._log_message(f"Error cloning repository: {err}", "result")
            raise RuntimeError(f"Error cloning repo: {err}")

        cwd = Path("/app") / self.github_info["repo"]
        await self._log_message(f"Repository cloned successfully to {cwd}", "result")

        return cwd

    async def _pip_package_setup(self) -> Path:
        assert self.stage == "setup", f"pip_package_setup can only be called during setup stage, current stage: {self.stage}"
        await self._log_message(f"Setting up pip package: {self.model_id}")

        cwd = Path("/app") / f"{self.model_id}-integration"

        _, err = await run_shell_code_in_container(
            f"mkdir -p {str(cwd)}",
            container_name=self.container_name
        )

        if err:
            await self._log_message(f"Error creating directory: {err}", "result")
            raise RuntimeError(f"Error creating directory: {err}")

        await self._log_message(f"Directory created successfully at {cwd}", "result")
        return cwd

    async def _install_python_version(self, python_version: str) -> None:
        assert self.stage == "setup", f"install_python_version can only be called during setup stage, current stage: {self.stage}"
        await self._log_message(f"Installing Python version: {python_version}")

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
                await self._log_message(f"Error installing Python version: {err}", "result")
                raise RuntimeError(f"Error installing python version: {err}")

        out, err = await run_shell_code_in_container(
            f"pyenv global {python_version}",
            container_name=self.container_name
        )

        if err:
            await self._log_message(f"Error setting global Python version: {err}", "result")
            raise RuntimeError(f"Error setting global python version: {err}")

        await self._log_message(f"Python {python_version} installed and set as global version", "result")
        return out

    async def _run_setup_script(self, setup_script: str) -> None:
        assert self.stage == "setup", f"run_setup_script can only be called during setup stage, current stage: {self.stage}"
        await self._log_message("Running setup script...")

        out, err = await run_shell_code_in_container(
            setup_script,
            container_name=self.container_name,
            cwd=f"/app/{self.github_info['repo']}"
        )

        if err:
            await self._log_message(f"Error running setup script: {err}", "result")
            raise RuntimeError(f"Error running setup script: {err}")

        await self._log_message("Setup script completed successfully", "result")
        return out

    async def _save_file_to_container(self, file_path: str, file_content: str) -> None:
        await create_file_in_container_with_content(
            file_path,
            file_content,
            container_name=self.container_name
        )

    async def _save_image(self) -> None:
        pass

    async def _run_agent(
            self,
            agent: Agent[Union[SetupDeps, ModelAnalysisDeps, PlannerDeps, InferenceDeps, TrainingDeps]],
            deps: Union[SetupDeps, ModelAnalysisDeps, PlannerDeps, InferenceDeps, TrainingDeps],
            message_history: list[ModelMessage] = None
    ) -> AgentRunResult[Union[SetupAgentOutputWithScript, ModelAnalysisAgentOutput, str, InferenceAgentOutputWithScript, TrainingAgentOutputWithScript]]:

        async with agent.iter(deps=deps, message_history=message_history) as run:
            async for node in run:
                if Agent.is_call_tools_node(node):
                    async with node.stream(run.ctx) as handle_stream:
                        async for event in handle_stream:
                            if isinstance(event, FunctionToolCallEvent):
                                message = f'[Tools] The LLM calls tool={event.part.tool_name!r} with args={event.part.args}'
                                await self._log_message(message)
                            # elif isinstance(event, FunctionToolResultEvent):
                            #     message = f'[Tools] Tool call {event.tool_call_id!r} returned => {event.result.content}'
                            #     await self._log_message(message)

        return run.result

    async def __call__(self) -> ModelIntegrationOutput:

        try:
            # SETUP STAGE
            await self.get_job()
            await self._update_job_status("running")
            await self._setup_container()
            self._set_stage("setup")

            if self.source == "github":
                container_cwd = await self._github_repo_setup()
            elif self.source == "pip":
                container_cwd = await self._pip_package_setup()
            else:
                raise ValueError(f"Invalid source: {self.source}")

            await self._log_message("Starting model setup analysis...")

            setup_run = await self._run_agent(
                self.setup_agent,
                SetupDeps(
                    model_id=self.model_id,
                    source=self.source,
                    container_name=self.container_name,
                    cwd=str(container_cwd),
                    integration_id=self.job_id
                )
            )

            await self._install_python_version(setup_run.output.python_version)

            # Install setup script to local machine
            model_save_dir = Path("models") / \
                str(self.user_id) / str(self.model_id)
            model_save_dir.mkdir(parents=True, exist_ok=True)
            with open(str(model_save_dir / "setup.sh"), "w") as f:
                f.write(setup_run.output.script)

            await create_model_integration_messages_pydantic(
                job_id=self.job_id,
                messages=setup_run.all_messages_json()
            )

            await self._log_message("Model setup completed successfully", "result")

            # ANALYSIS STAGE
            self._set_stage("analysis")
            await self._log_message("Starting model analysis...")
            model_analysis_run = await self._run_agent(
                self.model_analysis_agent,
                ModelAnalysisDeps(
                    model_id=self.model_id,
                    source=self.source,
                    container_name=self.container_name,
                    cwd=str(container_cwd),
                    python_version=setup_run.output.python_version,
                    integration_id=self.job_id
                )
            )

            await self._save_file_to_container(
                str(container_cwd / "config.py"),
                model_analysis_run.output.config_code
            )

            with open(str(model_save_dir / "config.py"), "w") as f:
                f.write(model_analysis_run.output.config_code)

            await create_model_integration_messages_pydantic(
                job_id=self.job_id,
                messages=model_analysis_run.all_messages_json()
            )

            await self._log_message(f"Model analysis completed. Found {len(model_analysis_run.output.supported_tasks)} supported task(s): {', '.join(model_analysis_run.output.supported_tasks)}", "result")
            planner_outputs, inference_outputs, training_outputs = [], [], []
            inference_save_paths, training_save_paths = [], []

            for task in model_analysis_run.output.supported_tasks:
                # PLANNING STAGE
                self._set_stage("planning", task)
                await self._log_message(f"Starting planning for task: {task}")

                planner_run = await self._run_agent(
                    self.planner_agent,
                    PlannerDeps(current_task=task,
                                modality=model_analysis_run.output.modality,
                                container_name=self.container_name,
                                cwd=str(container_cwd),
                                model_id=self.model_id,
                                source=self.source,
                                model_analysis=model_analysis_run.output,
                                integration_id=self.job_id)
                )

                planner_outputs.append(planner_run.output)
                await self._log_message(f"Planning completed for task: {task}", "result")

                await create_model_integration_messages_pydantic(
                    job_id=self.job_id,
                    messages=planner_run.all_messages_json()
                )

                # TRAINING STAGE
                self._set_stage("training", task)
                await self._log_message(f"Starting training implementation for task: {task}")
                training_run = await self._run_agent(
                    self.training_agent,
                    TrainingDeps(current_task=task,
                                 modality=model_analysis_run.output.modality,
                                 container_name=self.container_name,
                                 cwd=str(container_cwd),
                                 model_id=self.model_id,
                                 source=self.source,
                                 model_analysis=model_analysis_run.output,
                                 implementation_plan=planner_run.output,
                                 integration_id=self.job_id)
                )

                training_outputs.append(training_run.output)

                await create_model_integration_messages_pydantic(
                    job_id=self.job_id,
                    messages=training_run.all_messages_json()
                )

                await self._save_file_to_container(
                    str(container_cwd / f"training_{task}.py"),
                    training_run.output.script
                )

                await self._log_message(f"Training implementation completed for task: {task}", "result")

                # INFERENCE STAGE
                self._set_stage("inference", task)
                await self._log_message(f"Starting inference implementation for task: {task}")
                inference_run = await self._run_agent(
                    self.inference_agent,
                    InferenceDeps(current_task=task,
                                  training_script=training_run.output.script,
                                  modality=model_analysis_run.output.modality,
                                  container_name=self.container_name,
                                  cwd=str(container_cwd),
                                  model_id=self.model_id,
                                  source=self.source,
                                  model_analysis=model_analysis_run.output,
                                  implementation_plan=planner_run.output,
                                  integration_id=self.job_id)
                )

                inference_outputs.append(inference_run.output)

                await create_model_integration_messages_pydantic(
                    job_id=self.job_id,
                    messages=inference_run.all_messages_json()
                )

                await self._save_file_to_container(
                    str(container_cwd / f"inference_{task}.py"),
                    inference_run.output.script
                )

                await self._log_message(f"Inference implementation completed for task: {task}", "result")

                inference_save_dir = model_save_dir / "inference"
                training_save_dir = model_save_dir / "training"
                inference_save_dir.mkdir(parents=True, exist_ok=True)
                training_save_dir.mkdir(parents=True, exist_ok=True)

                with open(str(inference_save_dir / f"{task}.py"), "w") as f:
                    f.write(inference_run.output.script)
                with open(str(training_save_dir / f"{task}.py"), "w") as f:
                    f.write(training_run.output.script)

                inference_save_paths.append(
                    str(inference_save_dir / f"{task}.py"))
                training_save_paths.append(
                    str(training_save_dir / f"{task}.py"))

            # Final setup stage for saving model
            await self._log_message("Saving model to database...")
            model_id = uuid.uuid4()

            await insert_model(
                name=model_analysis_run.output.model_name,
                description=model_analysis_run.output.model_description,
                owner_id=self.user_id,
                public=False,
                modality_name=model_analysis_run.output.modality,
                source_name=self.source,
                programming_language_name="python",
                programming_language_version_name=setup_run.output.python_version,
                setup_script_path=str(model_save_dir / "setup.py"),
                config_script_path=str(model_save_dir / "config.py"),
                input_description=model_analysis_run.output.model_input_description,
                output_description=model_analysis_run.output.model_output_description,
                config_parameters=model_analysis_run.output.model_config_parameters,
                tasks=model_analysis_run.output.supported_tasks,
                inference_script_paths=inference_save_paths,
                training_script_paths=training_save_paths,
                model_id=model_id
            )

            await create_model_integration_result(
                job_id=self.job_id,
                model_id=model_id
            )

            # Save Redis stream messages to database
            streamed_nodes = await self.redis_stream.xread({str(self.job_id): 0}, count=None)
            integration_messages = []

            for item in streamed_nodes[0][1]:
                if item[1]["type"] in ["tool_call", "result"]:
                    message = item[1].copy()
                    message["timestamp"] = datetime.fromisoformat(
                        message["timestamp"]).replace(tzinfo=timezone.utc)

                    integration_messages.append(message)

            await create_model_integration_messages(self.job_id, integration_messages)

            await self._update_job_status("completed")
            await self._log_message(f"Model integration completed successfully! Model ID: {model_id}", "result")

            return ModelIntegrationOutput(
                setup_output=setup_run.output,
                model_analysis_output=model_analysis_run.output,
                planner_outputs=planner_outputs,
                inference_outputs=inference_outputs,
                training_outputs=training_outputs
            )

        except Exception as e:
            await self._log_message(f"Model integration failed: {str(e)}", "result")
            await self._update_job_status("failed")
            if self.container:
                self.container.stop()
                self.container.remove()
                self.container = None
            raise e


@broker.task(retry_on_error=False)
async def run_model_integration_task(
        user_id: str,
        model_id: str,
        job_id: uuid.UUID,
        source: Literal["github", "pip"] = "github") -> ModelIntegrationOutput:

    runner = ModelIntegrationRunner(user_id, model_id, job_id, source)
    result = await runner()
    return result
