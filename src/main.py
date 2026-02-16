from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    print("Closing database connections...")
    engine.dispose()
    print("Shutdown complete")

app = FastAPI(
    title="User Authentication API",
    version="2.0.0",
    lifespan=lifespan
)

# Enhanced CORS for Google OAuth
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost",
        "http://127.0.0.1",
        "https://accounts.google.com",
        "https://accounts.google.com:443",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

app.include_router(router)