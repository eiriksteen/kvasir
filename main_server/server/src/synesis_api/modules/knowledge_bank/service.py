import uuid
from sqlalchemy import select, or_, and_, func

from synesis_api.modules.function.service import get_functions
from synesis_api.database.service import fetch_all
from synesis_api.modules.function.models import function, function_definition
from synesis_api.modules.model.models import model, model_definition
from synesis_api.utils.rag_utils import embed
from synesis_schemas.main_server import QueryRequest, FunctionQueryResult, ModelQueryResult
from synesis_api.modules.model.service import get_models


async def query_functions(query_request: QueryRequest, exclude_model_functions: bool = True) -> FunctionQueryResult:

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

    return FunctionQueryResult(query_name=query_request.query_name, functions=functions)


async def query_models(user_id: uuid.UUID, query_request: QueryRequest) -> ModelQueryResult:

    query_vector = (await embed([query_request.query]))[0]

    model_query = select(
        model.c.id
    ).join(
        model_definition, model.c.definition_id == model_definition.c.id
    ).where(
        or_(model.c.user_id == user_id, model_definition.c.public == True)
    ).order_by(
        model.c.embedding.cosine_distance(query_vector)
    ).limit(query_request.k)

    model_records = await fetch_all(model_query)
    models = await get_models([m["id"] for m in model_records])

    return ModelQueryResult(query_name=query_request.query_name, models=models)
