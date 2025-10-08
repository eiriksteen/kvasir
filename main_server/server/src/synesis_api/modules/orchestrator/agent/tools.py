from pydantic_ai import RunContext
from pydantic_ai.exceptions import ModelRetry

from synesis_schemas.main_server import QueryRequest, ModelQueryResult, ModelEntityCreate, ModelEntityInDB, AddEntityToProject, FrontendNodeCreate
from synesis_api.modules.orchestrator.agent.deps import OrchestatorAgentDeps
from synesis_api.modules.knowledge_bank.service import query_models
from synesis_api.modules.model.service import create_model_entity
from synesis_api.modules.project.service import add_entity_to_project
from synesis_api.modules.node.service import create_node


async def search_existing_models(ctx: RunContext[OrchestatorAgentDeps], search_query: QueryRequest) -> ModelQueryResult:
    return await query_models(ctx.deps.user_id, search_query)


async def add_model_entity_to_project(ctx: RunContext[OrchestatorAgentDeps], model_entity_create: ModelEntityCreate) -> ModelEntityInDB:

    new_model_entity = await create_model_entity(ctx.deps.user_id, model_entity_create)
    await add_entity_to_project(AddEntityToProject(
        project_id=ctx.deps.project_id,
        entity_type="model_entity",
        entity_id=new_model_entity.id
    ))
    await create_node(FrontendNodeCreate(
        project_id=ctx.deps.project_id,
        type="model_entity",
        model_entity_id=new_model_entity.id
    ))

    return new_model_entity
