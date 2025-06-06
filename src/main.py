from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.flights.router import router as items_router
from src.storage.db import create_indexes


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator:
    await create_indexes()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(items_router, prefix="/flights", tags=["flights"])


@app.get("/")
def hello_world() -> str:
    return "Hello world"
