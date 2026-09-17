
import os

import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_slack_alert(message: str):
    """
    Send an ETL failure notification to Slack.

    The function does nothing when a Slack webhook
    is not configured.
    """

    if not SLACK_WEBHOOK_URL:
        return False

    payload = {
        "text": f"🚨 Zaalima ETL Alert\n{message}"
    }

    response = requests.post(
        SLACK_WEBHOOK_URL,
        json=payload,
        timeout=10
    )

    response.raise_for_status()

    return True


def airflow_failure_alert(context):
    """
    Airflow callback executed when an ETL task fails.
    """

    task_instance = context.get("task_instance")

    task_id = (
        task_instance.task_id
        if task_instance
        else "unknown"
    )

    dag_id = (
        task_instance.dag_id
        if task_instance
        else "unknown"
    )

    message = (
        f"ETL task failed.\n"
        f"DAG: {dag_id}\n"
        f"Task: {task_id}"
    )

    send_slack_alert(message)

