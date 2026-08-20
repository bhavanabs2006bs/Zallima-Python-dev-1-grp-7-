from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .core.config import settings
from sqlalchemy import create_engine, text

app = FastAPI(
    title="Media Processing Microservice",
    description="Event-driven backend for heavy async media processing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS media_jobs (
                id SERIAL PRIMARY KEY,
                job_id VARCHAR(36) UNIQUE NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                input_file VARCHAR(500),
                output_files TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT
            )
        """))
        conn.commit()
    engine.dispose()


@app.get("/")
async def root():
    return {"message": "Media Processing Microservice", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
