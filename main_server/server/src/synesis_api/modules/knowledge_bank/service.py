import uuid
from sqlalchemy import select, or_, and_, func
from typing import List

from synesis_api.modules.function.service import get_functions
from synesis_api.modules.model.service import get_models
from synesis_api.database.service import fetch_all
from synesis_api.modules.function.models import function, function_definition
from synesis_api.modules.model.models import model_implementation, model_definition
from synesis_api.utils.rag_utils import embed
from synesis_schemas.main_server import (
    FunctionQueryResult,
    ModelQueryResult,
    GetGuidelinesRequest,
    SearchFunctionsRequest,
    SearchModelsRequest
)
from synesis_api.modules.knowledge_bank.guidelines import TIME_SERIES_FORECASTING_GUIDELINES


async def query_functions(search_request: SearchFunctionsRequest, exclude_model_functions: bool = True) -> List[FunctionQueryResult]:

    results = []
    for query_request in search_request.queries:

        query_vector = (await embed([query_request.query]))[0]
        # For each fn definition id, get the max fn version
        max_version_subquery = select(function.c.definition_id, func.max(function.c.version).label(
            "newest_version")).group_by(function.c.definition_id).subquery("max_version_subquery")
        fn_id_of_max_version_subquery = select(function.c.id).join(
            max_version_subquery,
            and_(function.c.definition_id == max_version_subquery.c.definition_id,
                 function.c.version == max_version_subquery.c.newest_version)
        )

        function_query = select(
            function.c.id
        ).join(
            function_definition, function.c.definition_id == function_definition.c.id
        ).where(
            function.c.id.in_(fn_id_of_max_version_subquery)
        ).order_by(
            function.c.embedding.cosine_distance(query_vector)
        ).limit(query_request.k)

        if exclude_model_functions:
            function_query = function_query.where(
                and_(function_definition.c.type != "training", function_definition.c.type != "inference"))

        fns = await fetch_all(function_query)
        function_ids = [fn["id"] for fn in fns]
        functions = await get_functions(function_ids)

        results.append(FunctionQueryResult(
            query_name=query_request.query_name, functions=functions))

    return results


async def query_models(user_id: uuid.UUID, search_request: SearchModelsRequest) -> List[ModelQueryResult]:

    results = []
    for query_request in search_request.queries:

        query_vector = (await embed([query_request.query]))[0]

        # For each model definition id, get the max model version
        max_version_subquery = select(model_implementation.c.definition_id, func.max(model_implementation.c.version).label(
            "newest_version")).group_by(model_implementation.c.definition_id).subquery("max_version_subquery")
        model_id_of_max_version_subquery = select(model_implementation.c.id).join(
            max_version_subquery,
            and_(model_implementation.c.definition_id == max_version_subquery.c.definition_id,
                 model_implementation.c.version == max_version_subquery.c.newest_version)
        )

        model_query = select(
            model_implementation.c.id
        ).join(
            model_definition, model_implementation.c.definition_id == model_definition.c.id
        ).where(
            and_(
                model_implementation.c.id.in_(
                    model_id_of_max_version_subquery),
                or_(model_implementation.c.user_id == user_id,
                    model_definition.c.public == True)
            )
        ).order_by(
            model_implementation.c.embedding.cosine_distance(query_vector)
        ).limit(query_request.k)

        model_records = await fetch_all(model_query)
        if not model_records:
            models_found = []
        else:
            models_found = await get_models([m["id"] for m in model_records])

        results.append(ModelQueryResult(
            query_name=query_request.query_name, models=models_found))

    return results


def get_task_guidelines(request: GetGuidelinesRequest) -> str:
    if request.task == "time_series_forecasting":
        return TIME_SERIES_FORECASTING_GUIDELINES
    else:
        raise ValueError(f"Unsupported task: {request.task}")
