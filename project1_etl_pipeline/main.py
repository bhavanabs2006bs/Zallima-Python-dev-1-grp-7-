#!/usr/bin/env python3
"""Enterprise ETL Pipeline - Main Entry Point"""
import argparse
import sys
from .extractors import SalesforceExtractor, StripeExtractor
from .transformers import DataTransformer
from .loaders import WarehouseLoader
from .utils.logger import setup_logger
from .models.schemas import DataSource, JobStatus

logger = setup_logger("etl_pipeline", log_file="logs/etl_pipeline.log")


def run_full_pipeline(database_url: str):
    logger.info("=" * 60)
    logger.info("STARTING FULL ETL PIPELINE")
    logger.info("=" * 60)
    try:
        loader = WarehouseLoader(database_url)
        loader.create_tables()

        logger.info("\n[1/3] EXTRACTION")
        sf_extractor = SalesforceExtractor("mock_id", "mock_secret")
        sf_extractor.authenticate()
        sf_records = sf_extractor.extract_all(max_pages=2)

        stripe_extractor = StripeExtractor("sk_test_mock")
        stripe_extractor.authenticate()
        stripe_records = stripe_extractor.extract_all(max_pages=2)

        logger.info("\n[2/3] TRANSFORMATION")
        transformer = DataTransformer()
        sf_result = transformer.transform_salesforce(sf_records)
        stripe_result = transformer.transform_stripe(stripe_records)
        all_records = sf_result.data + stripe_result.data

        logger.info("\n[3/3] LOADING")
        job_id = loader.create_etl_job(DataSource.SALESFORCE)
        loaded = loader.upsert_records(all_records, job_id)
        loader.update_job_status(job_id, JobStatus.COMPLETED, len(all_records), loaded)

        logger.info("=" * 60)
        logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY")
        logger.info(f"Total records loaded: {loaded}")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


def show_job_history(database_url: str):
    loader = WarehouseLoader(database_url)
    history = loader.get_job_history(limit=10)
    print("\n" + "=" * 60)
    print("ETL JOB HISTORY")
    print("=" * 60)
    for job in history:
        print(f"Job {job['id']}: {job['source']} | {job['status']} | Extracted: {job['records_extracted']} | Loaded: {job['records_loaded']}")


def main():
    parser = argparse.ArgumentParser(description="Enterprise ETL Pipeline")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run full pipeline")
    run_parser.add_argument("--db-url", default="sqlite:///etl_database.db", help="Database URL")

    hist_parser = subparsers.add_parser("history", help="Show job history")
    hist_parser.add_argument("--db-url", default="sqlite:///etl_database.db", help="Database URL")

    args = parser.parse_args()
    if args.command == "run":
        run_full_pipeline(args.db_url)
    elif args.command == "history":
        show_job_history(args.db_url)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
