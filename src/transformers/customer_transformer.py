from typing import Any


def transform_customer(data: dict[str, Any], source: str) -> dict[str, Any]:
    """
    Convert customer data from different APIs
    into a common internal schema.
    """

    if source == "stripe":
        return {
            "source": "stripe",
            "customer_id": data.get("id"),
            "name": data.get("name"),
            "email": data.get("email"),
        }

    if source == "salesforce":
        return {
            "source": "salesforce",
            "customer_id": data.get("Id"),
            "name": data.get("Name"),
            "email": data.get("Email"),
        }

    raise ValueError(f"Unsupported source: {source}")