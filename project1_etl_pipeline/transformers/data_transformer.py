from datetime import datetime
from typing import List, Dict, Any

import pandas as pd

from ..models.schemas import (
    SalesforceContact,
    StripeTransaction,
    UnifiedRecord,
    TransformResult,
    DataSource,
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DataTransformer:
    """Transform and validate records from different data sources."""

    def __init__(self):
        self.stats = {
            "processed": 0,
            "failed": 0,
            "errors": [],
        }

    def transform_salesforce(
        self,
        records: List[Dict[str, Any]]
    ) -> TransformResult:
        """Transform Salesforce Contact records into UnifiedRecord objects."""

        transformed = []
        errors = []

        for record in records:
            self.stats["processed"] += 1

            try:
                first_name = record.get("FirstName") or ""
                last_name = record.get("LastName") or ""

                full_name = f"{first_name} {last_name}".strip()

                created_at = self._parse_datetime(
                    record.get("CreatedDate")
                )

                updated_at = self._parse_datetime(
                    record.get("LastModifiedDate")
                )

                unified_record = UnifiedRecord(
                    source=DataSource.SALESFORCE,
                    source_id=str(record["Id"]),
                    email=record.get("Email"),
                    name=full_name or None,
                    company=record.get("Company"),
                    amount=None,
                    currency=None,
                    status=None,
                    created_at=created_at,
                    updated_at=updated_at,
                    metadata={
                        "phone": record.get("Phone"),
                    },
                )

                transformed.append(
                    unified_record.model_dump()
                )

            except Exception as e:
                error_message = (
                    f"Salesforce record transformation failed: {e}"
                )

                logger.error(error_message)
                errors.append(error_message)

                self.stats["failed"] += 1
                self.stats["errors"].append(error_message)

        return TransformResult(
            success=len(errors) == 0,
            records_processed=len(records),
            records_failed=len(errors),
            errors=errors,
            data=transformed,
        )

    def transform_stripe(
        self,
        records: List[Dict[str, Any]]
    ) -> TransformResult:
        """Transform Stripe PaymentIntent records into UnifiedRecord objects."""

        transformed = []
        errors = []

        for record in records:
            self.stats["processed"] += 1

            try:
                created_timestamp = record.get("created")

                if created_timestamp is None:
                    raise ValueError(
                        "Stripe record is missing created timestamp"
                    )

                created_at = datetime.fromtimestamp(
                    created_timestamp
                )

                customer_id = record.get("customer")

                unified_record = UnifiedRecord(
                    source=DataSource.STRIPE,
                    source_id=str(record["id"]),
                    email=None,
                    name=record.get("description"),
                    company=None,
                    amount=record.get("amount"),
                    currency=record.get("currency"),
                    status=record.get("status"),
                    created_at=created_at,
                    updated_at=created_at,
                    metadata={
                        "customer_id": customer_id,
                        "description": record.get("description"),
                        "stripe_metadata": record.get(
                            "metadata",
                            {}
                        ),
                    },
                )

                transformed.append(
                    unified_record.model_dump()
                )

            except Exception as e:
                error_message = (
                    f"Stripe record transformation failed: {e}"
                )

                logger.error(error_message)
                errors.append(error_message)

                self.stats["failed"] += 1

                # Added for Stripe error tracking
                self.stats["errors"].append(error_message)

        return TransformResult(
            success=len(errors) == 0,
            records_processed=len(records),
            records_failed=len(errors),
            errors=errors,
            data=transformed,
        )

    def transform_to_dataframe(
        self,
        records: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """Convert transformed records into a Pandas DataFrame."""

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)

        # Keep Stripe amounts in cents.
        # This matches the UnifiedRecord / StripeTransaction schema.
        if "amount" in df.columns:
            df["amount"] = pd.to_numeric(
                df["amount"],
                errors="coerce"
            )

        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(
                df["created_at"],
                errors="coerce"
            )

        if "updated_at" in df.columns:
            df["updated_at"] = pd.to_datetime(
                df["updated_at"],
                errors="coerce"
            )

        return df

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        """Convert an API datetime value into a Python datetime."""

        if isinstance(value, datetime):
            return value

        if not value:
            raise ValueError("Datetime value is missing")

        value = str(value)

        # Salesforce commonly returns ISO timestamps
        # such as 2026-09-05T12:30:00.000+0000.
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        if value.endswith("+0000"):
            value = value[:-5] + "+00:00"

        return datetime.fromisoformat(value)