from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.db import init_db, init_pool, close_pool, get_connection
from backend.settings import settings
from backend.routers import preferences, homepage, explain

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_pool()
    try:
        init_db()
    except Exception as e:
        # DB connection could fail on local tests if no DB is available
        print(f"Warning: Failed to init db: {e}")
    yield
    # Shutdown
    close_pool()

app = FastAPI(title="Mausam Personalized Homepage API", lifespan=lifespan)

origins = [o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "PUT"],
    allow_headers=["*"],
)

app.include_router(preferences.router)
app.include_router(homepage.router)
app.include_router(explain.router)

@app.get("/health")
def health():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return {"status": "ok", "db": "connected"}
    except Exception:
        # We catch exceptions to prevent crash, instead returning degraded status.
        # Do not expose exception str() to UI to protect potential secrets in DSN traces.
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content={"status": "degraded", "db": "unavailable"})
