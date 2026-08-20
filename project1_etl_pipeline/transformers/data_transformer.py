import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
from ..models.schemas import SalesforceContact, StripeTransaction, UnifiedRecord, DataSource, TransformResult
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DataTransformer:
    def __init__(self):
        self.stats = {"processed": 0, "failed": 0, "errors": []}
        logger.info("DataTransformer initialized")

    def transform_salesforce(self, raw_data: List[Dict[str, Any]]) -> TransformResult:
        logger.info(f"Transforming {len(raw_data)} Salesforce records")
        transformed = []
        errors = []
        for record in raw_data:
            try:
                contact = SalesforceContact(
                    id=record["Id"], email=record["Email"],
                    first_name=record["FirstName"], last_name=record["LastName"],
                    company=record.get("Company"), phone=record.get("Phone"),
                    created_at=datetime.fromisoformat(record["CreatedDate"]),
                    updated_at=datetime.fromisoformat(record["LastModifiedDate"])
                )
                unified = UnifiedRecord(
                    source=DataSource.SALESFORCE, source_id=contact.id,
                    email=contact.email, name=f"{contact.first_name} {contact.last_name}",
                    company=contact.company, status="active",
                    created_at=contact.created_at, updated_at=contact.updated_at,
                    metadata={"phone": contact.phone}
                )
                transformed.append(unified)
                self.stats["processed"] += 1
            except Exception as e:
                errors.append(str(e))
                self.stats["failed"] += 1
                self.stats["errors"].append(str(e))
        return TransformResult(success=len(errors)==0, records_processed=len(transformed),
                               records_failed=len(errors), errors=errors,
                               data=[r.model_dump() for r in transformed])

    def transform_stripe(self, raw_data: List[Dict[str, Any]]) -> TransformResult:
        logger.info(f"Transforming {len(raw_data)} Stripe records")
        transformed = []
        errors = []
        for record in raw_data:
            try:
                transaction = StripeTransaction(
                    id=record["id"], customer_id=record["customer"],
                    amount=record["amount"], currency=record["currency"],
                    status=record["status"], description=record.get("description"),
                    created_at=datetime.fromtimestamp(record["created"])
                )
                unified = UnifiedRecord(
                    source=DataSource.STRIPE, source_id=transaction.id,
                    name=transaction.description, amount=transaction.amount,
                    currency=transaction.currency, status=transaction.status,
                    created_at=transaction.created_at, updated_at=transaction.created_at,
                    metadata={"customer_id": transaction.customer_id}
                )
                transformed.append(unified)
                self.stats["processed"] += 1
            except Exception as e:
                errors.append(str(e))
                self.stats["failed"] += 1
        return TransformResult(success=len(errors)==0, records_processed=len(transformed),
                               records_failed=len(errors), errors=errors,
                               data=[r.model_dump() for r in transformed])

    def transform_to_dataframe(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        for col in ["created_at", "updated_at"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        if "amount" in df.columns:
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce") / 100
        return df

    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()
