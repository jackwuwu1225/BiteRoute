import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    with open("data/restaurant.json", "r", encoding="utf-8") as fh:
        app.state.restaurants = json.load(fh)
    yield
    app.state.restaurants = []


app = FastAPI(title="BiteRoute API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
