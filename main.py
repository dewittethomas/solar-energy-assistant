from fastapi import FastAPI
from routers import predictions

app = FastAPI(title="Solar Energy Assistant API")

app.include_router(predictions.router)