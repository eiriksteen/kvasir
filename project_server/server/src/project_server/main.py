from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from project_server.modules.data_source_router import router as data_source_router
from project_server.modules.pipeline_router import router as pipeline_router
from project_server.modules.agent_router import router as agents_router
from project_server.modules.code_router import router as code_router
from project_server.modules.chart_router import router as chart_router
from project_server.modules.image_router import router as image_router
from project_server.modules.table_router import router as table_router


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


app.include_router(data_source_router,
                   prefix="/data-source", tags=["Data Source"])
app.include_router(pipeline_router, prefix="/pipeline", tags=["Pipeline"])
app.include_router(agents_router, prefix="/agents", tags=["Agents"])
app.include_router(chart_router, prefix="/chart", tags=["Chart"])
app.include_router(image_router, prefix="/image", tags=["Image"])
app.include_router(table_router, prefix="/table", tags=["Table"])
app.include_router(code_router, prefix="/code", tags=["Code"])
