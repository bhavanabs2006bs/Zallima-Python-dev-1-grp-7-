"""Apache Airflow DAG for ETL Pipeline - Standalone version"""
from datetime import datetime, timedelta
from ..extractors import SalesforceExtractor, StripeExtractor
from ..transformers import DataTransformer
from ..loaders import WarehouseLoader
from ..utils.logger import get_logger
from ..models.schemas import DataSource, JobStatus

logger = get_logger(__name__)


def run_etl_pipeline(database_url: str = "sqlite:///etl_database.db"):
    logger.info("=" * 60)
    logger.info("STARTING ETL PIPELINE")
    logger.info("=" * 60)

    loader = WarehouseLoader(database_url)
    loader.create_tables()

    # Extract Salesforce
    logger.info("[1/3] EXTRACTING SALESFORCE DATA")
    sf_extractor = SalesforceExtractor("mock_id", "mock_secret")
    sf_extractor.authenticate()
    sf_records = sf_extractor.extract_all(max_pages=2)

    # Extract Stripe
    logger.info("[1/3] EXTRACTING STRIPE DATA")
    stripe_extractor = StripeExtractor("sk_test_mock")
    stripe_extractor.authenticate()
    stripe_records = stripe_extractor.extract_all(max_pages=2)

    # Transform
    logger.info("[2/3] TRANSFORMING DATA")
    transformer = DataTransformer()
    sf_result = transformer.transform_salesforce(sf_records)
    stripe_result = transformer.transform_stripe(stripe_records)
    all_records = sf_result.data + stripe_result.data

    # Load
    logger.info("[3/3] LOADING TO WAREHOUSE")
    job_id = loader.create_etl_job(DataSource.SALESFORCE)
    loaded = loader.upsert_records(all_records, job_id)
    loader.update_job_status(job_id, JobStatus.COMPLETED, len(all_records), loaded)

    stats = transformer.get_stats()
    logger.info(f"Pipeline complete: {stats}")
    logger.info(f"Records loaded: {loaded}")
    logger.info("=" * 60)
    return {"records": loaded, "stats": stats}


if __name__ == "__main__":
    run_etl_pipeline()
