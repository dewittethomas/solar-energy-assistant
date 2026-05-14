from fastapi import FastAPI
from fastmcp import FastMCP
from routers import data_uploads, model_training, predictions

api = FastAPI(title="Solar Energy Assistant API")
api.include_router(predictions.router)
api.include_router(data_uploads.router)
api.include_router(model_training.router)

mcp = FastMCP("Solar Energy Assistant")

mcp_app = mcp.http_app(path='/')

app = FastAPI(lifespan=mcp_app.lifespan)
app.mount("/mcp", mcp_app)
app.include_router(data_uploads.router)
app.include_router(predictions.router)
app.include_router(model_training.router)
