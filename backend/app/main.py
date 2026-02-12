from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api.routes import auth, users, rag
from app.monitoring.prometheus_metrics import get_metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

    # Fix: ensure user_id column is nullable (may have been created as NOT NULL)
    try:
        with engine.connect() as conn:
            conn.execute(
                __import__("sqlalchemy").text(
                    "ALTER TABLE queries ALTER COLUMN user_id DROP NOT NULL"
                )
            )
            conn.commit()
            print("✅ queries.user_id set to nullable")
    except Exception:
        pass  # column already nullable or table doesn't exist yet

    yield
    # Shutdown


app = FastAPI(
    title=settings.APP_NAME,
    description="RAG system for biomedical equipment technical manuals",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(rag.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Welcome to MediAssist-Pro API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type="text/plain")
