from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config.database_config import engine, Base
from app.utils.exception_handlers import register_exception_handlers
from fastapi.middleware.cors import CORSMiddleware
from app.modules.auth.routers.guests_router import router as guest_router
from app.modules.auth.routers.users_router import router as user_router

# from app.modules.pms.routers.tenants_routers import router as tenant_router
# from app.modules.pms.routers.properties_routers import router as property_router

# from app.modules.pms.routers.room_routers import router as room_router
# from app.modules.pms.routers.room_units_routers import router as room_unit_router
from app.modules.auth.models import *
from app.modules.pms.models import *


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # shutdown
    await engine.dispose()


app = FastAPI(
    lifespan=lifespan, title="StayEasy API", version="1.0.0", root_path="/api/v1"
)
register_exception_handlers(app)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(guest_router)
app.include_router(user_router)
# app.include_router(tenant_router)
# app.include_router(property_router)
# app.include_router(room_router)
# app.include_router(room_unit_router)

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
