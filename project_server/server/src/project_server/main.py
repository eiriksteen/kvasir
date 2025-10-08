from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from project_server.modules.file_router import router as file_router
from project_server.modules.pipeline_router import router as pipeline_router
from project_server.modules.agent_router import router as agents_router
from project_server.modules.data_object_router import router as data_object_router

app = FastAPI(
    title="Project Server API",
    description="Project Server API",
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


app.include_router(file_router, prefix="/file", tags=["File"])
app.include_router(data_object_router,
                   prefix="/data-object", tags=["Data Object"])
app.include_router(pipeline_router, prefix="/pipeline", tags=["Pipeline"])
app.include_router(agents_router, prefix="/agents", tags=["Agents"])
