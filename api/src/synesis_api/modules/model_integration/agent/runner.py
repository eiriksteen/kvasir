import uuid
import docker
from pathlib import Path
from typing import Union, List, Literal
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
from synesis_api.base_schema import BaseSchema
from synesis_api.modules.model_integration.agent.setup_agent.agent import SetupDeps, SetupAgentOutputWithScript, setup_agent
from synesis_api.modules.model_integration.agent.model_analysis_agent.agent import ModelAnalysisDeps, ModelAnalysisAgentOutput, model_analysis_agent
from synesis_api.modules.model_integration.agent.planner_agent.agent import PlannerDeps, planning_agent
from synesis_api.modules.model_integration.agent.training_agent.agent import TrainingDeps, TrainingAgentOutputWithScript, training_agent
from synesis_api.modules.model_integration.agent.inference_agent.agent import InferenceDeps, InferenceAgentOutputWithScript, inference_agent


class ModelIntegrationOutput(BaseSchema):
    setup_output: SetupAgentOutputWithScript
    model_analysis_output: ModelAnalysisAgentOutput
    planner_outputs: List[str]
    training_outputs: List[TrainingAgentOutputWithScript]
    inference_outputs: List[InferenceAgentOutputWithScript]


class ModelIntegrationRunner:

    def __init__(
            self,
            model_id: str,
            source: Literal["github", "pip"] = "github",
            verbose: bool = False):

        self.setup_agent = setup_agent
        self.model_analysis_agent = model_analysis_agent
        self.planner_agent = planning_agent
        self.training_agent = training_agent
        self.inference_agent = inference_agent
        self.model_id = model_id
        self.source = source
        self.base_image = "model-integration-image"
        self.docker_client = docker.from_env()
        self.container = None
        self.integration_id = uuid.uuid4()
        self.container_name = f"model-integration-{self.integration_id}"
        self.verbose = verbose

        if source == "github":
            self.github_info = parse_github_url(model_id)
        elif source == "pip":
            self.github_info = None

    def get_integration_id(self) -> uuid.UUID:
        return self.integration_id

    async def _setup_container(self) -> None:
        # Is now sync, blocking the main thread, TODO: Make async
        self.container = self.docker_client.containers.create(
            self.base_image,
            name=self.container_name,
        )
        self.container.start()

    async def _github_repo_setup(self) -> Path:

        assert self.source == "github", "Can only clone from github for now"

        _, err = await run_shell_code_in_container(
            f"git clone {self.model_id}.git",
            container_name=self.container_name
        )

        if err:
            raise RuntimeError(f"Error cloning repo: {err}")

        cwd = Path("/app") / self.github_info["repo"]

        return cwd

    async def _pip_package_setup(self) -> Path:

        cwd = Path("/app") / f"{self.model_id}-integration"

        _, err = await run_shell_code_in_container(
            f"mkdir -p {str(cwd)}",
            container_name=self.container_name
        )

        if err:
            raise RuntimeError(f"Error creating directory: {err}")

        return cwd

    async def _install_python_version(self, python_version: str) -> None:
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
                raise RuntimeError(f"Error installing python version: {err}")

        out, err = await run_shell_code_in_container(
            f"pyenv global {python_version}",
            container_name=self.container_name
        )

        if err:
            raise RuntimeError(f"Error setting global python version: {err}")

        return out

    async def _run_setup_script(self, setup_script: str) -> None:
        out, err = await run_shell_code_in_container(
            setup_script,
            container_name=self.container_name,
            cwd=f"/app/{self.github_info['repo']}"
        )

        if err:
            raise RuntimeError(f"Error running setup script: {err}")

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
                                message = f'[Tools] The LLM calls tool={event.part.tool_name!r} with args={event.part.args} (tool_call_id={event.part.tool_call_id!r})'
                                if self.verbose:
                                    print(message[:100])
                            elif isinstance(event, FunctionToolResultEvent):
                                message = f'[Tools] Tool call {event.tool_call_id!r} returned => {event.result.content}'
                                if self.verbose:
                                    print(message[:100])

        return run.result

    async def __call__(self) -> ModelIntegrationOutput:

        try:
            await self._setup_container()

            if self.source == "github":
                cwd = await self._github_repo_setup()
            elif self.source == "pip":
                cwd = await self._pip_package_setup()
            else:
                raise ValueError(f"Invalid source: {self.source}")

            setup_run = await self._run_agent(
                self.setup_agent,
                SetupDeps(
                    model_id=self.model_id,
                    source=self.source,
                    container_name=self.container_name,
                    cwd=str(cwd),
                    integration_id=self.integration_id
                )
            )

            await self._install_python_version(setup_run.output.python_version)

            model_analysis_run = await self._run_agent(
                self.model_analysis_agent,
                ModelAnalysisDeps(
                    model_id=self.model_id,
                    source=self.source,
                    container_name=self.container_name,
                    cwd=str(cwd),
                    python_version=setup_run.output.python_version,
                    integration_id=self.integration_id
                )
            )

            await self._save_file_to_container(
                str(cwd / "config.py"),
                model_analysis_run.output.config_code
            )

            print("="*20, "REPO ANALYSIS DONE", "="*20)
            print(f"Repo analysis output: {model_analysis_run.output}")
            print("="*50)
            # await self._run_setup_script(setup_run.output.script)

            if self.verbose:
                print("="*20, "SETUP DONE", "="*20)
                print(f"Setup output: {setup_run.output}")
                print("="*50)

            planner_outputs, inference_outputs, training_outputs = [], [], []
            for task in model_analysis_run.output.supported_tasks:

                planner_run = await self._run_agent(
                    self.planner_agent,
                    PlannerDeps(current_task=task,
                                modality=model_analysis_run.output.modality,
                                container_name=self.container_name,
                                cwd=str(cwd),
                                model_id=self.model_id,
                                source=self.source,
                                model_analysis=model_analysis_run.output,
                                integration_id=self.integration_id)
                )

                planner_outputs.append(planner_run.output)

                training_run = await self._run_agent(
                    self.training_agent,
                    TrainingDeps(current_task=task,
                                 modality=model_analysis_run.output.modality,
                                 container_name=self.container_name,
                                 cwd=str(cwd),
                                 model_id=self.model_id,
                                 source=self.source,
                                 model_analysis=model_analysis_run.output,
                                 implementation_plan=planner_run.output,
                                 integration_id=self.integration_id)
                )

                training_outputs.append(training_run.output)

                await self._save_file_to_container(
                    str(cwd / f"training_{task}.py"),
                    training_run.output.script
                )

                if self.verbose:
                    print("="*20, f"TRAINING DONE FOR {task}", "="*20)
                    print(f"Training output: {training_run.output}")
                    print("="*50)

                training_outputs.append(training_run.output)

                inference_run = await self._run_agent(
                    self.inference_agent,
                    InferenceDeps(current_task=task,
                                  training_script=training_run.output.script,
                                  modality=model_analysis_run.output.modality,
                                  container_name=self.container_name,
                                  cwd=str(cwd),
                                  model_id=self.model_id,
                                  source=self.source,
                                  model_analysis=model_analysis_run.output,
                                  implementation_plan=planner_run.output,
                                  integration_id=self.integration_id)
                )

                inference_outputs.append(inference_run.output)

                await self._save_file_to_container(
                    str(cwd / f"inference_{task}.py"),
                    inference_run.output.script
                )

                if self.verbose:
                    print("="*20, f"INFERENCE DONE FOR {task}", "="*20)
                    print(f"Inference output: {inference_run.output}")
                    print("="*50)

            return ModelIntegrationOutput(
                setup_output=setup_run.output,
                model_analysis_output=model_analysis_run.output,
                planner_outputs=planner_outputs,
                inference_outputs=inference_outputs,
                training_outputs=training_outputs
            )

        except Exception as e:
            if self.container:
                self.container.stop()
                self.container.remove()
                self.container = None
            raise e
