from src.models import Customer


def validate_customer(data: dict) -> Customer:
    """
    Validate transformed customer data using Pydantic.
    """
    return Customer(
        id=data["customer_id"],
        name=data.get("name"),
        email=data.get("email")
    )