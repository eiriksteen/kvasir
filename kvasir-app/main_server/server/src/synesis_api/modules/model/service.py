from synesis_api.auth.schema import User
from synesis_api.auth.service import get_current_user
from fastapi import Depends
from typing import Annotated
import uuid
import jsonschema
from datetime import datetime, timezone
from typing import List  # , Optional
from sqlalchemy import select, insert, delete
from fastapi import HTTPException

from synesis_api.database.service import fetch_all, execute, fetch_one
from synesis_api.modules.model.models import (
    model_implementation,
    model,
    model_instantiated,
    model_function,
)
from kvasir_ontology.entities.model.data_model import (
    ModelBase,
    ModelImplementationBase,
    ModelImplementation,
    ModelFunctionBase,
    ModelInstantiatedBase,
    ModelInstantiated,
    Model,
    ModelCreate,
    ModelImplementationCreate,
    ModelInstantiatedCreate,
    # ModelFunctionCreate,
)
from kvasir_ontology.entities.model.interface import ModelInterface


class Models(ModelInterface):

    async def create_model(self, model_create: ModelCreate) -> Model:
        model_record = ModelBase(
            id=uuid.uuid4(),
            user_id=self.user_id,
            **model_create.model_dump(exclude={"implementation_create"}),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        await execute(insert(model).values(model_record.model_dump()), commit_after=True)

        implementation_obj = None
        if model_create.implementation_create:
            implementation_obj = await self.create_model_implementation(model_create.implementation_create)

        return Model(
            **model_record.model_dump(),
            implementation=implementation_obj
        )

    async def create_model_implementation(self, model_implementation_create: ModelImplementationCreate) -> Model:
        model_record = await self.get_model(model_implementation_create.model_id)
        if not model_record:
            raise HTTPException(
                status_code=404, detail=f"Model with id {model_implementation_create.model_id} not found")

        # Create training function
        training_function_obj = ModelFunctionBase(
            id=uuid.uuid4(),
            **model_implementation_create.training_function.model_dump(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        await execute(insert(model_function).values(**training_function_obj.model_dump()), commit_after=True)

        inference_function_obj = ModelFunctionBase(
            id=uuid.uuid4(),
            **model_implementation_create.inference_function.model_dump(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        await execute(insert(model_function).values(**inference_function_obj.model_dump()), commit_after=True)

        model_implementation_obj = ModelImplementationBase(
            id=model_record.id,
            **model_implementation_create.model_dump(exclude={"training_function", "inference_function"}),
            training_function_id=training_function_obj.id,
            inference_function_id=inference_function_obj.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        await execute(insert(model_implementation).values(**model_implementation_obj.model_dump()), commit_after=True)

        return await self.get_model(model_implementation_create.model_id)

    async def create_model_instantiated(self, model_instantiated_create: ModelInstantiatedCreate) -> ModelInstantiated:
        if model_instantiated_create.model_create:
            model_obj = await self.create_model(model_instantiated_create.model_create)

        else:
            assert model_instantiated_create.model_id, "model_id or model_create must be provided"
            model_obj = await self.get_model(model_instantiated_create.model_id)
            if not model_obj or model_obj.user_id != self.user_id:
                raise HTTPException(
                    status_code=404, detail="Model not found or access denied")

        if model_obj.implementation:
            try:
                jsonschema.validate(
                    model_instantiated_create.config,
                    model_obj.implementation.config_schema
                )
            except jsonschema.ValidationError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid config: {e.message}, schema: {model_obj.implementation.config_schema}"
                )

        model_instantiated_obj = ModelInstantiatedBase(
            id=uuid.uuid4(),
            user_id=self.user_id,
            **model_instantiated_create.model_dump(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        await execute(insert(model_instantiated).values(**model_instantiated_obj.model_dump()), commit_after=True)

        return ModelInstantiated(
            **model_instantiated_obj.model_dump(),
            model=model_obj
        )

    async def get_model(self, model_id: uuid.UUID) -> Model:
        models = await self.get_models([model_id])
        if not models:
            raise HTTPException(
                status_code=404, detail=f"Model with id {model_id} not found")
        return models[0]

    async def get_models(self, model_ids: List[uuid.UUID]) -> List[Model]:
        model_query = select(model).where(model.c.user_id == self.user_id)
        if model_ids:
            model_query = model_query.where(
                model.c.id.in_(model_ids))

        models = await fetch_all(model_query)

        if not models:
            return []

        model_ids_list = [m["id"] for m in models]

        # Fetch implementations
        model_implementation_query = select(model_implementation).where(
            model_implementation.c.id.in_(model_ids_list))
        model_implementations = await fetch_all(model_implementation_query)

        # Get all function IDs
        function_ids = []
        for impl in model_implementations:
            function_ids.append(impl["training_function_id"])
            function_ids.append(impl["inference_function_id"])

        # Query function records
        function_records = []
        if function_ids:
            function_query = select(model_function).where(
                model_function.c.id.in_(function_ids))
            function_records = await fetch_all(function_query)

        # Build output objects
        output_objs = []
        for model_id_val in model_ids_list:
            model_obj = ModelBase(**next(
                iter([m for m in models if m["id"] == model_id_val])))

            impl_record = next(iter([
                impl for impl in model_implementations if impl["id"] == model_id_val]), None)

            implementation_obj = None
            if impl_record:
                # Get function records for this implementation
                training_function_record = next(
                    (f for f in function_records if f["id"] == impl_record["training_function_id"]), None)
                inference_function_record = next(
                    (f for f in function_records if f["id"] == impl_record["inference_function_id"]), None)

                if training_function_record and inference_function_record:
                    training_function_obj = ModelFunctionBase(
                        **training_function_record)
                    inference_function_obj = ModelFunctionBase(
                        **inference_function_record)

                    implementation_obj = ModelImplementation(
                        **impl_record,
                        training_function=training_function_obj,
                        inference_function=inference_function_obj
                    )

            output_objs.append(Model(
                **model_obj.model_dump(),
                implementation=implementation_obj
            ))

        return output_objs

    async def get_model_instantiated(self, model_instantiated_id: uuid.UUID) -> ModelInstantiated:
        models_instantiated = await self.get_models_instantiated([model_instantiated_id])
        if not models_instantiated:
            raise HTTPException(
                status_code=404, detail=f"Model instantiated with id {model_instantiated_id} not found")
        return models_instantiated[0]

    async def get_models_instantiated(self, model_instantiated_ids: List[uuid.UUID]) -> List[ModelInstantiated]:
        model_instantiated_query = select(model_instantiated).where(
            model_instantiated.c.user_id == self.user_id)
        if model_instantiated_ids:
            model_instantiated_query = model_instantiated_query.where(
                model_instantiated.c.id.in_(model_instantiated_ids))

        model_instantiated_records = await fetch_all(model_instantiated_query)

        if not model_instantiated_records:
            return []

        # Get all model IDs
        model_ids_list = [record["model_id"]
                          for record in model_instantiated_records]
        models_dict = {m.id: m for m in await self.get_models(model_ids_list)}

        output_objs = []
        for record in model_instantiated_records:
            model_obj = models_dict.get(record["model_id"])
            if not model_obj:
                raise HTTPException(
                    status_code=404,
                    detail=f"Model with id {record['model_id']} not found for model instantiated {record['id']}")
            output_objs.append(ModelInstantiated(
                **record,
                model=model_obj
            ))

        return output_objs

    async def delete_model(self, model_id: uuid.UUID) -> None:
        model_obj = await self.get_model(model_id)
        if not model_obj or model_obj.user_id != self.user_id:
            raise HTTPException(
                status_code=404, detail="Model not found or access denied")

        await execute(delete(model_implementation).where(model_implementation.c.id == model_id), commit_after=True)
        await execute(delete(model).where(model.c.id == model_id), commit_after=True)

    async def delete_model_instantiated(self, model_instantiated_id: uuid.UUID) -> None:
        model_instantiated_obj = await self.get_model_instantiated(model_instantiated_id)
        if not model_instantiated_obj or model_instantiated_obj.user_id != self.user_id:
            raise HTTPException(
                status_code=404, detail="Model instantiated not found or access denied")

        await execute(delete(model_instantiated).where(model_instantiated.c.id == model_instantiated_id), commit_after=True)
        await self.delete_model(model_instantiated_obj.model_id)


# For dependency injection


async def get_models_service(user: Annotated[User, Depends(get_current_user)]) -> ModelInterface:
    return Models(user.id)
