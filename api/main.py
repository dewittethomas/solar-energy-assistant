from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP

from core.settings import get_settings
from routers import datasets, model_training, predictions, recommendations, users

settings = get_settings()

mcp = FastMCP("Solar Energy Assistant")
mcp_app = mcp.http_app(path='/')

app = FastAPI(
    title='Solar Energy Assistant API',
    lifespan=mcp_app.lifespan
)
app.mount("/mcp", mcp_app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)
app.include_router(datasets.router)
app.include_router(predictions.router)
app.include_router(recommendations.router)
app.include_router(model_training.router)
app.include_router(users.router)
