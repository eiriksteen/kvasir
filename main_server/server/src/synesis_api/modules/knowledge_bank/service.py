from sqlalchemy import select

from synesis_api.database.service import fetch_all
from synesis_api.modules.function.models import (
    function, function_input_structure, function_output_structure, function_output_variable
)
from synesis_api.modules.model.models import model
from synesis_api.modules.model_sources.models import model_source
from synesis_api.utils.rag_utils import embed
from synesis_schemas.main_server import QueryRequest, FunctionQueryResult, ModelQueryResult, ModelSourceQueryResult, FunctionBare, ModelBare, ModelSourceBare


async def query_functions(query_request: QueryRequest) -> FunctionQueryResult:

    query_vector = (await embed([query_request.query]))[0]

    function_query = select(
        function
    ).order_by(
        function.c.embedding.cosine_distance(query_vector)
    ).limit(query_request.k)

    fns = await fetch_all(function_query)

    function_ids = [fn["id"] for fn in fns]

    function_input_structures_query = select(function_input_structure).where(
        function_input_structure.c.function_id.in_(function_ids))

    function_output_structures_query = select(function_output_structure).where(
        function_output_structure.c.function_id.in_(function_ids))

    function_output_variables_query = select(function_output_variable).where(
        function_output_variable.c.function_id.in_(function_ids))

    fn_inputs = await fetch_all(function_input_structures_query)
    fn_outputs = await fetch_all(function_output_structures_query)
    fn_output_variables = await fetch_all(function_output_variables_query)

    return FunctionQueryResult(query_name=query_request.query_name, functions=[FunctionBare(
        **f,
        input_structures=fn_inputs,
        output_structures=fn_outputs,
        output_variables=fn_output_variables) for f in fns]
    )


async def query_models(query_request: QueryRequest) -> ModelQueryResult:

    query_vector = (await embed([query_request.query]))[0]

    model_query = select(
        model
    ).order_by(
        model.c.embedding.cosine_distance(query_vector)
    ).limit(query_request.k)

    models = await fetch_all(model_query)

    return ModelQueryResult(query_name=query_request.query_name, models=[ModelBare(
        **m) for m in models]
    )


async def query_model_sources(query_request: QueryRequest) -> ModelSourceQueryResult:

    query_vector = (await embed([query_request.query]))[0]

    model_source_query = select(
        model_source
    ).order_by(
        model_source.c.embedding.cosine_distance(query_vector)
    ).limit(query_request.k)

    model_sources = await fetch_all(model_source_query)

    return ModelSourceQueryResult(query_name=query_request.query_name, model_sources=[ModelSourceBare(
        **m) for m in model_sources]
    )
