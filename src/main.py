from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from contextlib import asynccontextmanager
from .models import Base
from .db import engine
from .router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized")

    yield
    print("Closing database connections... ")
    engine.dispose()
    print("Shutdown complete")

app = FastAPI(
    title="User Authentication API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for OAuth popup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
