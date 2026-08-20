import pytest
import os
import tempfile
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    db_path = os.path.join(tempfile.gettempdir(), "test_media_jobs.db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    
    from app.main import app
    engine = create_engine(f"sqlite:///{db_path}")
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
    yield TestClient(app)


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Media Processing" in response.json()["message"]


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_jobs(client):
    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
