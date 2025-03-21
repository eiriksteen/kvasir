import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .auth.router import router as auth_router
from .data_integration.router import router as data_integration_router
from .eda.router import router as eda_router
from .ontology.router import router as ontology_router
from .secrets import CACHE_URL


app = FastAPI(
    title="Synesis API",
    description="Synesis API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router,
                   prefix="/auth",
                   tags=["Authentication"])

app.include_router(data_integration_router,
                   prefix="/data",
                   tags=["Data Integration"])

app.include_router(ontology_router,
                   prefix="/ontology",
                   tags=["Ontology"])

app.include_router(eda_router,
                   prefix="/eda",
                   tags=["Exploratory Data Analysis"])



@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = redis.Redis(host=CACHE_URL)
    yield
    await app.state.redis.close()


@app.get("/")
async def root():
    return {"message": "Welcome to the Synesis API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
