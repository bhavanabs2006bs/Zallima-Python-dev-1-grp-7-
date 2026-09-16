"""
Apache Airflow DAG for Enterprise ETL Pipeline.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from project1_etl_pipeline.main import run_full_pipeline


# ============================================================
# DEFAULT 
# ============================================================

default_args = {
    "owner": "etl_team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


# ============================================================
# ETL TASK
# ============================================================

def run_pipeline():
    """Run the complete ETL pipeline."""

    run_full_pipeline(
        database_url="sqlite:///etl_database.db"
    )


# ============================================================
# AIRFLOW DAG
# ============================================================

with DAG(
    dag_id="enterprise_etl_pipeline",
    default_args=default_args,
    description="Enterprise ETL pipeline for Salesforce and Stripe",
    schedule="0 2 * * *",
    start_date=datetime(2026, 9, 1),
    catchup=False,
    max_active_runs=1,
    tags=["etl", "salesforce", "stripe", "s3"],
) as dag:

    run_etl = PythonOperator(
        task_id="run_etl_pipeline",
        python_callable=run_pipeline,
    )


# ============================================================
# TASK FLOW
# ============================================================

run_etl