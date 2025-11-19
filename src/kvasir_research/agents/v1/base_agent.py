from abc import ABC, abstractmethod
from uuid import UUID
from typing import Literal, Optional, List, AsyncGenerator, Tuple, TypeVar, Generic, Any
from typing_extensions import Self
from pydantic import BaseModel, ValidationError, TypeAdapter
from dataclasses import dataclass, fields
from collections import OrderedDict
from pydantic_ai.messages import ModelMessage
from pydantic_ai import Agent

from kvasir_research.agents.v1.callbacks import KvasirV1Callbacks
from kvasir_research.sandbox.local import LocalSandbox
from kvasir_research.sandbox.modal import ModalSandbox
from kvasir_ontology.ontology import Ontology
from kvasir_research.sandbox.abstract import AbstractSandbox

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

    def __post_init__(self):
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

        if isinstance(self.user_id, str):
            self.user_id = UUID(self.user_id)
        if isinstance(self.project_id, str):
            self.project_id = UUID(self.project_id)
        if self.run_id and isinstance(self.run_id, str):
            self.run_id = UUID(self.run_id)

    @staticmethod
    def _convert_uuid_list(items: List) -> List[UUID]:
        return [UUID(item) if isinstance(item, str) else item for item in items]

    def _get_non_serializable_fields(self) -> set:
        return {"sandbox", "ontology", "callbacks", "bearer_token"}

    def _convert_ordered_dict_to_dict(self, obj: Any) -> Any:
        if isinstance(obj, OrderedDict):
            return {k: self._convert_ordered_dict_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, dict):
            return {k: self._convert_ordered_dict_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._convert_ordered_dict_to_dict(item) for item in obj]
        else:
            return obj

    def to_dict(self) -> dict:
        non_serializable = self._get_non_serializable_fields()
        deps_dict = {}
        for field in fields(self):
            field_name = field.name
            if field_name not in non_serializable:
                value = getattr(self, field_name)
                deps_dict[field_name] = self._convert_ordered_dict_to_dict(
                    value)
        return deps_dict


class BaseAgentOutput(BaseModel):
    response: str


class AgentV1(ABC, Generic[TDeps, TOutput]):
    deps_class: type[TDeps]

    def __init__(self, deps: TDeps, agent: Agent[TDeps, TOutput]):
        self.deps = deps
        self.agent = agent
        self.message_history: Optional[List[ModelMessage]] = None

    @abstractmethod
    async def __call__(self, prompt: str) -> TOutput:
        pass

    @abstractmethod
    async def _setup_run(self) -> UUID:
        pass

    async def _run_agent(self, prompt: str) -> TOutput:
        response = await self.agent.run(
            prompt,
            deps=self.deps,
            message_history=self.message_history
        )

        if self.message_history is None:
            self.message_history = response.all_messages()
        else:
            self.message_history += response.new_messages()

        return response.output

    async def _run_agent_streaming(self, prompt: str) -> AsyncGenerator[Tuple[TOutput, bool], None]:
        async with self.agent.run_stream(
            prompt,
            deps=self.deps,
            message_history=self.message_history
        ) as run:
            async for message, last in run.stream_responses(debounce_by=0.01):
                try:
                    output = await run.validate_response_output(
                        message,
                        allow_partial=not last
                    )
                    yield output, last
                except ValidationError:
                    continue

            if self.message_history is None:
                self.message_history = run.all_messages()
            else:
                self.message_history += run.new_messages()

    async def finish_run(self, success_message: Optional[str] = None):
        assert self.deps.run_id is not None, "Run ID must be set before finishing run."
        await self.deps.callbacks.save_message_history(self.deps.user_id, self.deps.run_id, self.message_history)
        await self.deps.callbacks.set_run_status(self.deps.user_id, self.deps.run_id, "completed")
        if success_message:
            await self.deps.callbacks.log(self.deps.user_id, self.deps.run_id, success_message, "result")
        await self.save_deps()

    async def fail_run_if_exists(self, error: str):
        if self.deps.run_id is not None:
            await self.deps.callbacks.set_run_status(self.deps.user_id, self.deps.run_id, "failed")
            await self.deps.callbacks.log(self.deps.user_id, self.deps.run_id, error, "error")
            await self.deps.callbacks.save_message_history(self.deps.user_id, self.deps.run_id, self.message_history)
            await self.save_deps()

    @classmethod
    async def from_run(cls, user_id: UUID, run_id: UUID, callbacks: KvasirV1Callbacks, bearer_token: Optional[str] = None) -> Self:
        deps = await cls.load_deps(user_id, run_id, callbacks, bearer_token)
        agent = cls(deps)
        agent.message_history = await callbacks.get_message_history(user_id, run_id)
        return agent

    async def save_deps(self):
        assert self.deps.run_id is not None, "Run ID must be set before saving deps."
        deps_dict = self.deps.to_dict()
        jsonable_dict = TypeAdapter(Any).dump_python(deps_dict, mode='json')
        await self.deps.callbacks.save_deps(self.deps.user_id, self.deps.run_id, jsonable_dict)

    @classmethod
    async def load_deps(cls, user_id: UUID, run_id: UUID, callbacks: KvasirV1Callbacks, bearer_token: Optional[str] = None):
        deps_dict = await callbacks.load_deps(user_id, run_id)
        if not deps_dict:
            raise ValueError(
                "No deps found for run. If you created the run outside the first agent run, you must init through deps. ")
        deps_dict["callbacks"] = callbacks
        deps_dict["bearer_token"] = bearer_token
        return cls.deps_class(**deps_dict)
