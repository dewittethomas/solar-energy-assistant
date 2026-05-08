from fastapi import FastAPI
from fastmcp import FastMCP
from routers import predictions

api = FastAPI(title="Solar Energy Assistant API")
api.include_router(predictions.router)

mcp = FastMCP("Solar Energy Assistant")

mcp_app = mcp.http_app(path='/')

app = FastAPI(lifespan=mcp_app.lifespan)
app.mount("/mcp", mcp_app)
app.include_router(predictions.router) 