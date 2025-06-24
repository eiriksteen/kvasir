from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from synesis_api.modules.jobs.router import router as jobs_router
from synesis_api.worker import broker
from contextlib import asynccontextmanager
from synesis_api.auth.router import router as auth_router
from synesis_api.modules.data_integration.router import router as integration_router
from synesis_api.modules.chat.router import router as chat_router
from synesis_api.modules.analysis.router import router as eda_router
from synesis_api.modules.automation.router import router as automation_router
from synesis_api.modules.ontology.router import router as ontology_router
from synesis_api.modules.data_provider.router import router as data_provider_router
from synesis_api.modules.project.router import router as project_router
from synesis_api.modules.node.router import router as node_router


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


app.include_router(chat_router,
                   prefix="/chat",
                   tags=["Chat"])


# Include routers
app.include_router(auth_router,
                   prefix="/auth",
                   tags=["Authentication"])


app.include_router(integration_router,
                   prefix="/integration",
                   tags=["Integration"])


app.include_router(ontology_router,
                   prefix="/ontology",
                   tags=["Ontology"])


app.include_router(eda_router,
                   prefix="/analysis",
                   tags=["Analysis"])


app.include_router(automation_router,
                   prefix="/automation",
                   tags=["AI Automation"])


app.include_router(jobs_router,
                   prefix="",
                   tags=["Jobs"])

app.include_router(project_router,
                   prefix="/project",
                   tags=["Project"])

app.include_router(node_router,
                   prefix="/node",
                   tags=["Node"])


app.include_router(data_provider_router,
                   prefix="/data-provider",
                   tags=["Data Provider"])


@app.get("/")
async def root():
    return {"message": "Welcome to the Synesis API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
