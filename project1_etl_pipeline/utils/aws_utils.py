import boto3
import json
from typing import Optional
from datetime import datetime

from .logger import get_logger


logger = get_logger(__name__)


class S3Handler:

    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1"
    ):
        self.bucket_name = bucket_name

        session_kwargs = {
            "region_name": region_name
        }

        if aws_access_key_id and aws_secret_access_key:
            session_kwargs["aws_access_key_id"] = aws_access_key_id
            session_kwargs["aws_secret_access_key"] = aws_secret_access_key

        self.s3_client = boto3.client(
            "s3",
            **session_kwargs
        )

        logger.info(
            f"S3Handler initialized for bucket: {bucket_name}"
        )

    def upload_json(
        self,
        data: list,
        source: str,
        extraction_date: Optional[str] = None
    ) -> str:

        if extraction_date is None:
            extraction_date = datetime.now().strftime(
                "%Y-%m-%d"
            )

        timestamp = datetime.now().strftime(
            "%H-%M-%S"
        )

        key = (
            f"raw/{source}/"
            f"{extraction_date}/"
            f"{timestamp}/"
            f"data.json"
        )

        json_data = json.dumps(
            data,
            default=str
        )

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json_data,
            ContentType="application/json"
        )

        logger.info(
            f"Uploaded {len(data)} records to "
            f"s3://{self.bucket_name}/{key}"
        )

        return key

    def download_json(
        self,
        key: str
    ) -> list:

        response = self.s3_client.get_object(
            Bucket=self.bucket_name,
            Key=key
        )

        data = json.loads(
            response["Body"]
            .read()
            .decode("utf-8")
        )

        logger.info(
            f"Downloaded {len(data)} records from "
            f"s3://{self.bucket_name}/{key}"
        )

        return data