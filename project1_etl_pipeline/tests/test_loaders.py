import pytest
from datetime import datetime
from ..loaders import WarehouseLoader
from ..models.schemas import DataSource, JobStatus


class TestWarehouseLoader:
    def setup_method(self):
        self.loader = WarehouseLoader("sqlite:///:memory:")
        self.loader.create_tables()

    def test_create_etl_job(self):
        job_id = self.loader.create_etl_job(DataSource.SALESFORCE)
        assert job_id is not None

    def test_upsert_records(self):
        job_id = self.loader.create_etl_job(DataSource.SALESFORCE)
        records = [{"source": "salesforce", "source_id": "SF1", "email": "t@t.com", "name": "T U",
                     "company": "Corp", "amount": None, "currency": None, "status": "active",
                     "created_at": datetime.now(), "updated_at": datetime.now(), "metadata": {}}]
        loaded = self.loader.upsert_records(records, job_id)
        assert loaded == 1
