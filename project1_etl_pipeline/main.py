#!/usr/bin/env python3
"""Enterprise ETL Pipeline - Main Entry Point."""

import argparse
import os

from dotenv import load_dotenv

from .extractors import SalesforceExtractor, StripeExtractor
from .transformers import DataTransformer
from .loaders import WarehouseLoader
from .utils.aws_utils import S3Handler
from .utils.logger import setup_logger
from .models.schemas import DataSource, JobStatus


load_dotenv()

logger = setup_logger(
    "etl_pipeline",
    log_file="logs/etl_pipeline.log"
)


def run_full_pipeline(database_url: str):
    """Run the complete ETL pipeline with incremental extraction."""

    logger.info("=" * 60)
    logger.info("STARTING ETL PIPELINE")
    logger.info("=" * 60)

    loader = WarehouseLoader(database_url)

    try:
        loader.create_tables()

        # ============================================================
        # 1. EXTRACTION
        # ============================================================

        logger.info("\n[1/3] EXTRACTION")

        # -------------------------
        # Salesforce
        # -------------------------

        salesforce_vars = [
            "SALESFORCE_CLIENT_ID",
            "SALESFORCE_CLIENT_SECRET",
        ]

        missing_vars = [
            var
            for var in salesforce_vars
            if not os.getenv(var)
        ]

        if missing_vars:
            raise ValueError(
                "Missing Salesforce environment variables: "
                + ", ".join(missing_vars)
            )

        sf_extractor = SalesforceExtractor(
            client_id=os.getenv("SALESFORCE_CLIENT_ID"),
            client_secret=os.getenv("SALESFORCE_CLIENT_SECRET"),
        )

        if not sf_extractor.authenticate():
            raise ValueError(
                "Salesforce authentication failed"
            )

        sf_last_run = loader.get_last_successful_run(
            DataSource.SALESFORCE
        )

        if sf_last_run:
            logger.info(
                "Salesforce incremental extraction since: "
                f"{sf_last_run}"
            )
        else:
            logger.info(
                "No previous successful Salesforce run found. "
                "Performing full extraction."
            )

        sf_records = sf_extractor.extract_contacts(
            since=sf_last_run
        )

        logger.info(
            f"Salesforce records extracted: "
            f"{len(sf_records)}"
        )

        # -------------------------
        # Stripe
        # -------------------------

        stripe_key = os.getenv("STRIPE_SECRET_KEY")

        if not stripe_key:
            raise ValueError(
                "STRIPE_SECRET_KEY is not set in the .env file"
            )

        stripe_extractor = StripeExtractor(
            stripe_key
        )

        if not stripe_extractor.authenticate():
            raise ValueError(
                "Stripe authentication failed"
            )

        stripe_last_run = loader.get_last_successful_run(
            DataSource.STRIPE
        )

        if stripe_last_run:
            logger.info(
                "Stripe incremental extraction since: "
                f"{stripe_last_run}"
            )
        else:
            logger.info(
                "No previous successful Stripe run found. "
                "Performing full extraction."
            )

        stripe_records = stripe_extractor.extract_transactions(
            since=stripe_last_run
        )

        logger.info(
            f"Stripe records extracted: "
            f"{len(stripe_records)}"
        )
        # ============================================================
        # RAW DATA STORAGE - S3
        # ============================================================

        s3_bucket = os.getenv("S3_BUCKET_NAME")

        aws_region = os.getenv(
            "AWS_REGION",
            "us-east-1"
        )

        if s3_bucket:

            logger.info(
                "\nUploading raw extracted data to S3..."
            )

            s3_handler = S3Handler(
                bucket_name=s3_bucket,
                region_name=aws_region
            )

            sf_s3_key = s3_handler.upload_json(
            sf_records,
            source="salesforce"
            )

            stripe_s3_key = s3_handler.upload_json(
            stripe_records,
            source="stripe"
            )

            logger.info(
                f"Salesforce raw data uploaded: {sf_s3_key}"
            )

            logger.info(
                f"Stripe raw data uploaded: {stripe_s3_key}"
            )

        else:

            logger.warning(
                "S3_BUCKET_NAME is not configured. "
                "Skipping raw S3 upload."
            )
        # ============================================================
        # 2. TRANSFORMATION
        # ============================================================

        logger.info("\n[2/3] TRANSFORMATION")

        transformer = DataTransformer()

        sf_result = transformer.transform_salesforce(
            sf_records
        )

        stripe_result = transformer.transform_stripe(
            stripe_records
        )

        all_records = (
            sf_result.data +
            stripe_result.data
        )

        logger.info(
            "Total records after transformation: "
            f"{len(all_records)}"
        )
    
        # ============================================================
        # 3. LOADING
        # ============================================================

        logger.info("\n[3/3] LOADING")

        # -------------------------
        # Salesforce job
        # -------------------------

        sf_job_id = loader.create_etl_job(
            DataSource.SALESFORCE
        )

        sf_loaded = loader.upsert_records(
            sf_result.data,
            sf_job_id
        )

        loader.update_job_status(
            sf_job_id,
            JobStatus.COMPLETED,
            len(sf_records),
            sf_loaded
        )

        # -------------------------
        # Stripe job
        # -------------------------

        stripe_job_id = loader.create_etl_job(
            DataSource.STRIPE
        )

        stripe_loaded = loader.upsert_records(
            stripe_result.data,
            stripe_job_id
        )

        loader.update_job_status(
            stripe_job_id,
            JobStatus.COMPLETED,
            len(stripe_records),
            stripe_loaded
        )

        # -------------------------
        # Final summary
        # -------------------------

        total_loaded = (
            sf_loaded +
            stripe_loaded
        )

        logger.info("=" * 60)
        logger.info(
            "ETL PIPELINE COMPLETED SUCCESSFULLY"
        )
        logger.info(
            f"Salesforce loaded: {sf_loaded}"
        )
        logger.info(
            f"Stripe loaded: {stripe_loaded}"
        )
        logger.info(
            f"Total records loaded: {total_loaded}"
        )
        logger.info("=" * 60)

    except Exception as e:
        logger.error(
            f"Pipeline failed: {e}"
        )
        raise


def show_job_history(database_url: str):
    """Display recent ETL job history."""

    loader = WarehouseLoader(database_url)
    loader.create_tables()

    history = loader.get_job_history(limit=10)

    print("\n" + "=" * 60)
    print("ETL JOB HISTORY")
    print("=" * 60)

    if not history:
        print("No ETL jobs found.")
        return

    for job in history:
        print(
            f"Job {job['id']}: "
            f"{job['source']} | "
            f"{job['status']} | "
            f"Extracted: {job['records_extracted']} | "
            f"Loaded: {job['records_loaded']}"
        )


def main():
    """Command-line entry point."""

    parser = argparse.ArgumentParser(
        description="Enterprise ETL Pipeline"
    )

    subparsers = parser.add_subparsers(
        dest="command"
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run ETL pipeline"
    )

    run_parser.add_argument(
        "--db-url",
        default="sqlite:///etl_database.db",
        help="Database URL"
    )

    history_parser = subparsers.add_parser(
        "history",
        help="Show ETL job history"
    )

    history_parser.add_argument(
        "--db-url",
        default="sqlite:///etl_database.db",
        help="Database URL"
    )

    args = parser.parse_args()

    if args.command == "run":
        run_full_pipeline(
            args.db_url
        )

    elif args.command == "history":
        show_job_history(
            args.db_url
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()