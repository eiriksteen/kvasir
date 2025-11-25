from abc import ABC, abstractmethod
from uuid import UUID
from typing import List
from kvasir_ontology.entities.model.data_model import Model, ModelCreate, ModelImplementation, ModelImplementationCreate, ModelInstantiatedCreate, ModelInstantiated


class ModelInterface(ABC):

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    @abstractmethod
    async def create_model(self, model: ModelCreate) -> Model:
        pass

    @abstractmethod
    async def create_model_implementation(self, model_implementation: ModelImplementationCreate) -> Model:
        pass

    @abstractmethod
    async def create_model_instantiated(self, model_instantiated: ModelInstantiatedCreate) -> ModelInstantiated:
        pass

    @abstractmethod
    async def get_model(self, model_id: UUID) -> Model:
        pass

    @abstractmethod
    async def get_models(self, model_ids: List[UUID]) -> List[Model]:
        pass

    @abstractmethod
    async def get_model_instantiated(self, model_instantiated_id: UUID) -> ModelInstantiated:
        pass

    @abstractmethod
    async def get_models_instantiated(self, model_instantiated_ids: List[UUID]) -> List[ModelInstantiated]:
        pass

    @abstractmethod
    async def delete_model(self, model_id: UUID) -> None:
        pass

    @abstractmethod
    async def delete_model_instantiated(self, model_instantiated_id: UUID) -> None:
        pass
