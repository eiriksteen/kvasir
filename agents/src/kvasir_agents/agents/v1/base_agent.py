from uuid import UUID
from typing import Literal, Optional, List, AsyncGenerator, Tuple, TypeVar, Generic, Any, Union, Set
from typing_extensions import Self
from abc import ABC, abstractmethod
from pydantic import ValidationError, TypeAdapter
from dataclasses import dataclass, field
from pydantic_ai.messages import ModelMessage
from pydantic_ai import Agent

from kvasir_agents.agents.v1.callbacks import KvasirV1Callbacks
from kvasir_agents.sandbox.local import LocalSandbox
from kvasir_agents.sandbox.modal import ModalSandbox
from kvasir_ontology.ontology import Ontology
from kvasir_agents.sandbox.abstract import AbstractSandbox
from kvasir_agents.agents.v1.data_model import Context

TDeps = TypeVar('TDeps', bound='AgentDeps')
TOutput = TypeVar('TOutput')


@dataclass
class AgentDeps:
    user_id: UUID
    project_id: UUID
    package_name: str
    callbacks: KvasirV1Callbacks
    sandbox_type: Literal["local", "modal"]
    bearer_token: Optional[str] = None
    sandbox: Optional[AbstractSandbox] = None
    ontology: Optional[Ontology] = None
    run_name: Optional[str] = None
    run_id: Optional[UUID] = None
    max_entities_in_context: int = 10
    entities_in_context: Set[UUID] = field(default_factory=set)

    def __post_init__(self):
        if isinstance(self.user_id, str):
            self.user_id = UUID(self.user_id)
        if isinstance(self.project_id, str):
            self.project_id = UUID(self.project_id)
        if self.run_id and isinstance(self.run_id, str):
            self.run_id = UUID(self.run_id)

        if self.sandbox is None:
            if self.sandbox_type == "local":
                self.sandbox = LocalSandbox(self.project_id, self.package_name)
            elif self.sandbox_type == "modal":
                self.sandbox = ModalSandbox(self.project_id, self.package_name)
            else:
                raise ValueError(f"Invalid sandbox type: {self.sandbox_type}")

        if self.ontology is None:
            self.ontology = self.callbacks.create_ontology(
                self.user_id, self.project_id, self.bearer_token)

        if isinstance(self.entities_in_context, list):
            self.entities_in_context = set(self.entities_in_context)

    def to_dict(self) -> dict:
        return {
            "user_id": str(self.user_id),
            "project_id": str(self.project_id),
            "package_name": self.package_name,
            "sandbox_type": self.sandbox_type,
            "run_name": self.run_name,
            "run_id": str(self.run_id) if self.run_id else None,
            "max_entities_in_context": self.max_entities_in_context,
            "entities_in_context": [str(entity_id) for entity_id in list(self.entities_in_context)]
            # We exclude bearer_token, sandbox, and ontology
        }


class AgentV1(ABC, Generic[TDeps, TOutput]):
    deps_class: type[TDeps]

    def __init__(self, deps: TDeps, agent: Agent[TDeps, TOutput]):
        self.deps = deps
        self.agent = agent
        self.message_history: Optional[List[ModelMessage]] = None
        self.new_messages: List[ModelMessage] = []

    async def __call__(
            self,
            prompt: str,
            context: Optional[Context] = None,
            injections: Optional[List[str]] = None) -> TOutput:

        await self._setup_run()
        prompt = await self._setup_context(prompt, context, injections)
        run = await self.agent.run(prompt, deps=self.deps, message_history=self.message_history)

        if self.message_history is None:
            self.message_history = run.new_messages()
            self.new_messages = run.new_messages()
        else:
            self.message_history += run.new_messages()
            self.new_messages += run.new_messages()

        await self.finish_run(f"Agent run [{self.deps.run_name or self.deps.run_id}] completed")
        return run.output

    async def run_agent_streaming(
            self,
            prompt: str,
            context: Optional[Context] = None,
            injections: Optional[List[str]] = None) -> AsyncGenerator[Tuple[TOutput, bool], None]:

        await self._setup_run()
        prompt = await self._setup_context(prompt, context, injections)

        try:
            async with self.agent.run_stream(
                prompt,
                deps=self.deps,
                message_history=self.message_history
            ) as run:
                async for message, last in run.stream_responses(debounce_by=0.01):
                    try:
                        print(f"Message: {message}")
                        output = await run.validate_response_output(
                            message,
                            allow_partial=not last
                        )
                        yield output, last
                    except ValidationError:
                        continue

            if self.message_history is None:
                self.message_history = run.new_messages()
                self.new_messages = run.new_messages()
            else:
                self.message_history += run.new_messages()
                self.new_messages += run.new_messages()

            await self.finish_run(f"Agent run [{self.deps.run_name or self.deps.run_id}] completed")
        except Exception as e:
            await self.fail_run_if_exists(f"Error running agent [{self.deps.run_name or self.deps.run_id}]: {e}")
            raise e

    async def run_agent_text_stream(
            self,
            prompt: str,
            context: Optional[Context] = None,
            injections: Optional[List[str]] = None) -> AsyncGenerator[str, None]:

        await self._setup_run()
        prompt = await self._setup_context(prompt, context, injections)

        try:
            async with self.agent.run_stream(
                prompt,
                deps=self.deps,
                message_history=self.message_history,
                output_type=str
            ) as run:
                prev_text = ""
                async for output_text in run.stream_output(debounce_by=0.01):
                    if output_text != prev_text:
                        yield output_text
                        prev_text = output_text

            if self.message_history is None:
                self.message_history = run.new_messages()
                self.new_messages = run.new_messages()
            else:
                self.message_history += run.new_messages()
                self.new_messages += run.new_messages()

            await self.finish_run(f"Agent run [{self.deps.run_name or self.deps.run_id}] completed")
        except Exception as e:
            await self.fail_run_if_exists(f"Error running agent [{self.deps.run_name or self.deps.run_id}]: {e}")
            raise e

    async def finish_run(self, success_message: Optional[str] = None):
        assert self.deps.run_id is not None, "Run ID must be set before finishing run."
        await self.deps.callbacks.save_message_history(self.deps.user_id, self.deps.run_id, self.new_messages)
        await self.deps.callbacks.set_run_status(self.deps.user_id, self.deps.run_id, "completed")
        if success_message:
            await self.deps.callbacks.log(self.deps.user_id, self.deps.run_id, success_message, "result")
        await self.save_deps()

    async def fail_run_if_exists(self, error: str):
        if self.deps.run_id is not None:
            await self.deps.callbacks.set_run_status(self.deps.user_id, self.deps.run_id, "failed")
            await self.deps.callbacks.log(self.deps.user_id, self.deps.run_id, error, "error")
            await self.deps.callbacks.save_message_history(self.deps.user_id, self.deps.run_id, self.new_messages)
            await self.save_deps()

    async def save_deps(self):
        assert self.deps.run_id is not None, "Run ID must be set before saving deps."
        deps_dict = self.deps.to_dict()
        jsonable_dict = TypeAdapter(Any).dump_python(deps_dict, mode='json')

        await self.deps.callbacks.save_deps(self.deps.user_id, self.deps.run_id, jsonable_dict)

    async def _setup_context(
            self,
            prompt: str,
            context: Optional[Context] = None,
            injections: Optional[List[str]] = None) -> str:

        if injections:
            for injection in injections:
                prompt = f"{prompt}\n\n{injection}"

        if context:
            new_entities = set(context.data_sources) | set(context.datasets) | set(
                context.analyses) | set(context.pipelines) | set(context.models)

            if len(self.deps.entities_in_context | new_entities) > self.deps.max_entities_in_context:
                if len(new_entities) <= self.deps.max_entities_in_context:
                    # Override existing ones in this case, as the user preferences are prioritized
                    self.deps.entities_in_context = new_entities
                else:
                    raise ValueError(
                        f"Max entities in context reached: {len(new_entities)} > {self.deps.max_entities_in_context}")
            else:
                self.deps.entities_in_context.update(new_entities)

            context_desc = await self.deps.ontology.describe_entities(list(self.deps.entities_in_context))
            prompt = f"{prompt}\n\n<entity_context>\n\n{context_desc}\n\n</entity_context>"

        return prompt

    @abstractmethod
    async def _setup_run(self) -> UUID:
        pass

    @classmethod
    async def from_run(cls, user_id: UUID, run_id: UUID, callbacks: KvasirV1Callbacks, bearer_token: Optional[str] = None) -> Self:
        deps = await cls.load_deps(user_id, run_id, callbacks, bearer_token)
        agent = cls(deps)
        agent.message_history = await callbacks.get_message_history(user_id, run_id)
        return agent

    @classmethod
    async def load_deps(cls, user_id: UUID, run_id: UUID, callbacks: KvasirV1Callbacks, bearer_token: Optional[str] = None):
        deps_dict = await callbacks.load_deps(user_id, run_id)
        if not deps_dict:
            raise ValueError(
                "No deps found for run. If you created the run outside the first agent run, you must init through deps. ")
        deps_dict["callbacks"] = callbacks
        deps_dict["bearer_token"] = bearer_token
        return cls.deps_class(**deps_dict)
