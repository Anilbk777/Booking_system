from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.models import users_model
from app.config.database_config import Base, engine
from app.utils.exception_handlers import register_exception_handlers
from app.routers.user_router import router as user_router
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # shutdown
    await engine.dispose()


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)

app.include_router(user_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Easy Booking System API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
