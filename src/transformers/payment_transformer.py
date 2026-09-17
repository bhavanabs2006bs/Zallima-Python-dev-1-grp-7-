
from typing import Any


def transform_payment(
    data: dict[str, Any],
    source: str
) -> dict[str, Any]:
    """
    Convert payment data from different APIs
    into a common internal schema.
    """

    if source == "stripe":
        return {
            "source": "stripe",
            "payment_id": data.get("id"),
            "customer_id": data.get("customer"),
            "amount": data.get("amount"),
            "currency": data.get("currency"),
            "status": data.get("status"),
        }

    if source == "salesforce":
        return {
            "source": "salesforce",
            "payment_id": data.get("Id"),
            "customer_id": data.get("CustomerId"),
            "amount": data.get("Amount"),
            "currency": data.get("Currency"),
            "status": data.get("Status"),
        }

    raise ValueError(
        f"Unsupported source: {source}"
    )
