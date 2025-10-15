import uuid
from sqlalchemy import select, or_, and_, func
from typing import Union

from synesis_api.modules.function.service import get_functions
from synesis_api.database.service import fetch_all
from synesis_api.modules.function.models import function, function_definition
from synesis_api.modules.model.models import model, model_definition
from synesis_api.utils.rag_utils import embed
from synesis_schemas.main_server import (
    FunctionQueryResult,
    ModelQueryResult,
    GetGuidelinesRequest,
    FunctionQueryResultBare,
    ModelQueryResultBare,
    SearchFunctionsRequest,
    SearchModelsRequest
)
from synesis_api.modules.model.service import get_models
from synesis_api.modules.knowledge_bank.guidelines import TIME_SERIES_FORECASTING_GUIDELINES


async def query_functions(search_request: SearchFunctionsRequest, exclude_model_functions: bool = True) -> Union[FunctionQueryResult, FunctionQueryResultBare]:

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

        output_model = FunctionQueryResult if not search_request.bare else FunctionQueryResultBare
        results.append(output_model(
            query_name=query_request.query_name, functions=functions))

    return results


async def query_models(user_id: uuid.UUID, search_request: SearchModelsRequest) -> Union[ModelQueryResult, ModelQueryResultBare]:

    results = []
    for query_request in search_request.queries:

        query_vector = (await embed([query_request.query]))[0]

        # For each model definition id, get the max model version
        max_version_subquery = select(model.c.definition_id, func.max(model.c.version).label(
            "newest_version")).group_by(model.c.definition_id).subquery("max_version_subquery")
        model_id_of_max_version_subquery = select(model.c.id).join(
            max_version_subquery,
            and_(model.c.definition_id == max_version_subquery.c.definition_id,
                 model.c.version == max_version_subquery.c.newest_version)
        )

        model_query = select(
            model.c.id
        ).join(
            model_definition, model.c.definition_id == model_definition.c.id
        ).where(
            and_(
                model.c.id.in_(model_id_of_max_version_subquery),
                or_(model.c.user_id == user_id,
                    model_definition.c.public == True)
            )
        ).order_by(
            model.c.embedding.cosine_distance(query_vector)
        ).limit(query_request.k)

        model_records = await fetch_all(model_query)
        models = await get_models([m["id"] for m in model_records])

        output_model = ModelQueryResult if not search_request.bare else ModelQueryResultBare
        results.append(output_model(
            query_name=query_request.query_name, models=[m.model_dump() for m in models]))

    return results


def get_task_guidelines(request: GetGuidelinesRequest) -> str:
    if request.task == "time_series_forecasting":
        return TIME_SERIES_FORECASTING_GUIDELINES
    else:
        raise ValueError(f"Unsupported task: {request.task}")
