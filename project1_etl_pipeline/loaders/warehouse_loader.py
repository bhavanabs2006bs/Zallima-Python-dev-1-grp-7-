from sqlalchemy import create_engine, text
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from ..models.schemas import ETLJob, JobStatus, DataSource
from ..utils.logger import get_logger

logger = get_logger(__name__)


class WarehouseLoader:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        logger.info("WarehouseLoader initialized")

    def create_tables(self):
        sql = """
        CREATE TABLE IF NOT EXISTS etl_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            records_extracted INTEGER DEFAULT 0,
            records_loaded INTEGER DEFAULT 0,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT
        );
        CREATE TABLE IF NOT EXISTS unified_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source VARCHAR(50) NOT NULL,
            source_id VARCHAR(100) NOT NULL,
            email VARCHAR(255),
            name VARCHAR(200),
            company VARCHAR(200),
            amount REAL,
            currency VARCHAR(10),
            status VARCHAR(50),
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            metadata TEXT,
            etl_job_id INTEGER,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source, source_id)
        );
        """
        with self.engine.connect() as conn:
            for statement in sql.strip().split(";"):
                if statement.strip():
                    conn.execute(text(statement))
            conn.commit()
        logger.info("Database tables created")

    def create_etl_job(self, source: DataSource) -> int:
        with self.engine.connect() as conn:
            result = conn.execute(
                text("INSERT INTO etl_jobs (source, status, started_at) VALUES (:source, :status, :started_at)"),
                {"source": source.value, "status": "running", "started_at": datetime.now()}
            )
            conn.commit()
            job_id = result.lastrowid
            logger.info(f"Created ETL job {job_id}")
            return job_id

    def upsert_records(self, records: List[Dict[str, Any]], etl_job_id: int) -> int:
        if not records:
            return 0
        loaded = 0
        with self.engine.connect() as conn:
            for record in records:
                meta = record.get("metadata", {})
                if isinstance(meta, dict):
                    meta = json.dumps(meta, default=str)
                conn.execute(
                    text("""INSERT INTO unified_records (source, source_id, email, name, company, amount, currency, status, created_at, updated_at, metadata, etl_job_id)
                             VALUES (:source, :source_id, :email, :name, :company, :amount, :currency, :status, :created_at, :updated_at, :metadata, :etl_job_id)
                             ON CONFLICT(source, source_id) DO UPDATE SET email=excluded.email, name=excluded.name, company=excluded.company,
                             amount=excluded.amount, currency=excluded.currency, status=excluded.status, updated_at=excluded.updated_at, metadata=excluded.metadata"""),
                    {"source": record["source"], "source_id": record["source_id"], "email": record.get("email"),
                     "name": record.get("name"), "company": record.get("company"), "amount": record.get("amount"),
                     "currency": record.get("currency"), "status": record.get("status"),
                     "created_at": record.get("created_at"), "updated_at": record.get("updated_at"),
                     "metadata": meta, "etl_job_id": etl_job_id}
                )
                loaded += 1
            conn.commit()
        logger.info(f"Upserted {loaded} records")
        return loaded

    def update_job_status(self, job_id: int, status: JobStatus, records_extracted: int = 0, records_loaded: int = 0, error_message: Optional[str] = None):
        with self.engine.connect() as conn:
            conn.execute(
                text("UPDATE etl_jobs SET status=:status, records_extracted=:re, records_loaded=:rl, completed_at=:ca, error_message=:em WHERE id=:id"),
                {"id": job_id, "status": status.value, "re": records_extracted, "rl": records_loaded,
                 "ca": datetime.now() if status in [JobStatus.COMPLETED, JobStatus.FAILED] else None, "em": error_message}
            )
            conn.commit()

    def get_job_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM etl_jobs ORDER BY id DESC LIMIT :limit"), {"limit": limit})
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]

    def get_record_count(self, source: Optional[DataSource] = None) -> int:
        with self.engine.connect() as conn:
            if source:
                result = conn.execute(text("SELECT COUNT(*) FROM unified_records WHERE source=:s"), {"s": source.value})
            else:
                result = conn.execute(text("SELECT COUNT(*) FROM unified_records"))
            return result.scalar()
