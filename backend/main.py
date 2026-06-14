from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import engine, Base
from backend.routers import auth, patients, metrics, reports, trends, dashboard, shares, medications
from backend.migrations.runner import run_migrations

app = FastAPI(title=settings.APP_NAME, docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(metrics.router)
app.include_router(reports.router)
app.include_router(trends.router)
app.include_router(dashboard.router)
app.include_router(shares.router)
app.include_router(medications.router)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(run_migrations)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
