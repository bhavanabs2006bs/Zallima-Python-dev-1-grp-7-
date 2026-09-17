id="q2x8mp"
from src.models import Payment


def validate_payment(
    data: dict
) -> Payment:
    """
    Validate transformed payment data
    using the Pydantic Payment model.
    """

    return Payment(
        id=data["payment_id"],
        customer_id=data.get("customer_id"),
        amount=data.get("amount"),
        currency=data.get("currency"),
        status=data.get("status")
    )

