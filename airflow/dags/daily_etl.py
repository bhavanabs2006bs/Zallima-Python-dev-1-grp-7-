

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from src.config import STRIPE_API_KEY
from src.stripe_extractor import fetch_all_stripe_customers
from src.pipeline.etl_pipeline import process_customers
from src.utils.alerts import airflow_failure_alert


def run_stripe_etl():
    """
    Extract Stripe customers and process them
    through the ETL pipeline.
    """

    if not STRIPE_API_KEY:
        raise ValueError(
            "STRIPE_API_KEY is not configured."
        )

    customers = fetch_all_stripe_customers(
        STRIPE_API_KEY
    )

    stripe_data = {
        "data": customers
    }

    process_customers(
        stripe_data,
        "stripe"
    )


default_args = {
    "owner": "zaalima-project",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": airflow_failure_alert,
}


with DAG(
    dag_id="zaalima_daily_etl",
    default_args=default_args,
    description="Daily ETL pipeline for Stripe customer data",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["zaalima", "etl", "stripe"],
) as dag:

    stripe_etl_task = PythonOperator(
        task_id="stripe_customer_etl",
        python_callable=run_stripe_etl,
    )

