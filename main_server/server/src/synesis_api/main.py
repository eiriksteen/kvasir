from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from synesis_api.auth.router import router as auth_router
from synesis_api.modules.data_sources.router import router as data_sources_router
from synesis_api.modules.orchestrator.router import router as orchestrator_router
from synesis_api.modules.analysis.router import router as analysis_router
from synesis_api.modules.data_objects.router import router as data_objects_router
from synesis_api.modules.pipeline.router import router as pipeline_router
from synesis_api.modules.runs.router import router as runs_router
from synesis_api.modules.model.router import router as model_router
from synesis_api.modules.ontology.router import router as ontology_router
from synesis_api.modules.entity_graph.router import router as entity_graph_router
from synesis_api.modules.visualization.router import router as visualization_router
from synesis_api.modules.waitlist.router import router as waitlist_router
from synesis_api.modules.project.router import router as project_router
from synesis_api.modules.codebase.router import router as codebase_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Synesis API",
    description="Synesis API",
    version="1.0.0",
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(orchestrator_router,
                   prefix="/orchestrator",
                   tags=["Orchestrator"])


app.include_router(auth_router,
                   prefix="/auth",
                   tags=["Authentication"])


app.include_router(data_sources_router,
                   prefix="/data-sources",
                   tags=["Data Sources"])


app.include_router(data_objects_router,
                   prefix="/data-objects",
                   tags=["Data Objects"])


app.include_router(analysis_router,
                   prefix="/analysis",
                   tags=["Analysis"])


app.include_router(pipeline_router,
                   prefix="/pipeline",
                   tags=["Pipeline"])


app.include_router(runs_router,
                   prefix="/runs",
                   tags=["Runs"])


app.include_router(model_router,
                   prefix="/model",
                   tags=["Model"])


app.include_router(ontology_router,
                   prefix="/ontology",
                   tags=["Ontology"])


app.include_router(entity_graph_router,
                   prefix="/entity-graph",
                   tags=["Entity Graph"])


app.include_router(visualization_router,
                   prefix="/visualization",
                   tags=["Visualization"])


app.include_router(waitlist_router,
                   prefix="/waitlist",
                   tags=["Waitlist"])


app.include_router(project_router,
                   prefix="/project",
                   tags=["Project"])


app.include_router(codebase_router,
                   prefix="/codebase",
                   tags=["Codebase"])


@app.get("/")
async def root():
    return {"message": "Welcome to the Synesis API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
