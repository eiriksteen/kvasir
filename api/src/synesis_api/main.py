from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from synesis_api.worker import broker
from contextlib import asynccontextmanager
from synesis_api.auth.router import router as auth_router
from synesis_api.modules.data_sources.router import router as data_sources_router
from synesis_api.modules.orchestrator.router import router as orchestrator_router
from synesis_api.modules.analysis.router import router as analysis_router
from synesis_api.modules.data_objects.router import router as ontology_router
from synesis_api.modules.raw_data_storage.router import router as raw_data_storage_router
from synesis_api.modules.project.router import router as project_router
from synesis_api.modules.node.router import router as node_router
from synesis_api.modules.automation.router import router as automation_router
from synesis_api.modules.runs.router import router as runs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.startup()
    yield
    await broker.shutdown()

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


# Include routers
app.include_router(auth_router,
                   prefix="/auth",
                   tags=["Authentication"])


app.include_router(data_sources_router,
                   prefix="/data-sources",
                   tags=["Data Sources"])


app.include_router(ontology_router,
                   prefix="/data-objects",
                   tags=["Data Objects"])


app.include_router(analysis_router,
                   prefix="/analysis",
                   tags=["Analysis"])


app.include_router(project_router,
                   prefix="/project",
                   tags=["Project"])


app.include_router(node_router,
                   prefix="/node",
                   tags=["Node"])


app.include_router(raw_data_storage_router,
                   prefix="/raw-data-storage",
                   tags=["Raw Data Storage"])


app.include_router(automation_router,
                   prefix="/automation",
                   tags=["Automation"])


app.include_router(runs_router,
                   prefix="/runs",
                   tags=["Runs"])


@app.get("/")
async def root():
    return {"message": "Welcome to the Synesis API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
