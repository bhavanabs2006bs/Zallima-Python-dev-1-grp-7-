id="w7m8n2"
import json
from pathlib import Path
from datetime import datetime

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_S3_BUCKET
)

RAW_DATA_DIR = Path("data/raw")


def save_raw_json(data, source: str):
    """
    Save raw API response locally as JSON.
    """

    RAW_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    file_path = RAW_DATA_DIR / (
        f"{source}_{timestamp}.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            default=str
        )

    return file_path


def upload_raw_json_to_s3(
    data,
    source: str
):
    """
    Upload raw API response to AWS S3.

    Returns the S3 object key if successful.
    """

    if not AWS_ACCESS_KEY_ID:
        raise ValueError(
            "AWS_ACCESS_KEY_ID is not configured."
        )

    if not AWS_SECRET_ACCESS_KEY:
        raise ValueError(
            "AWS_SECRET_ACCESS_KEY is not configured."
        )

    if not AWS_S3_BUCKET:
        raise ValueError(
            "AWS_S3_BUCKET is not configured."
        )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    s3_key = (
        f"raw/{source}/"
        f"{source}_{timestamp}.json"
    )

    json_data = json.dumps(
        data,
        indent=4,
        default=str
    )

    try:

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )

        s3_client.put_object(
            Bucket=AWS_S3_BUCKET,
            Key=s3_key,
            Body=json_data.encode("utf-8"),
            ContentType="application/json"
        )

        return s3_key

    except (BotoCoreError, ClientError) as error:

        raise RuntimeError(
            f"Failed to upload raw data to S3: {error}"
        ) from error
