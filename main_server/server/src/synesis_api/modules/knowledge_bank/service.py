from sqlalchemy import select

from synesis_api.database.service import fetch_all
from synesis_api.modules.pipeline.models import (
    function, function_input, function_output
)
from synesis_schemas.main_server import FunctionWithoutEmbedding
from synesis_api.utils.rag_utils import embed
from synesis_schemas.main_server import SearchFunctionsResponse


async def search_functions(search_query: str, k: int = 10) -> SearchFunctionsResponse:

    query_vector = (await embed([search_query]))[0]

    function_query = select(
        function
    ).order_by(
        function.c.embedding.cosine_distance(query_vector)
    ).limit(k)

    fns = await fetch_all(function_query)

    function_ids = [fn["id"] for fn in fns]

    function_input_structures_query = select(function_input).where(
        function_input.c.function_id.in_(function_ids))

    function_output_structures_query = select(function_output).where(
        function_output.c.function_id.in_(function_ids))

    fn_inputs = await fetch_all(function_input_structures_query)
    fn_outputs = await fetch_all(function_output_structures_query)

    return SearchFunctionsResponse(functions=[FunctionWithoutEmbedding(**f, inputs=fn_inputs, outputs=fn_outputs) for f in fns])
