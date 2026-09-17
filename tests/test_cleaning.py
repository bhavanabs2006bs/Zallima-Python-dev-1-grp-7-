
from src.transformers.cleaning import (
    clean_customers,
    clean_payments
)


def test_clean_customers():
    records = [
        {
            "customer_id": "cus_001",
            "name": "  Bhavana  ",
            "email": " BHAVANA@EXAMPLE.COM "
        },
        {
            "customer_id": "cus_001",
            "name": "Duplicate",
            "email": "duplicate@example.com"
        }
    ]

    result = clean_customers(records)

    assert len(result) == 1
    assert result[0]["customer_id"] == "cus_001"
    assert result[0]["name"] == "Bhavana"
    assert result[0]["email"] == "bhavana@example.com"


def test_clean_payments():
    records = [
        {
            "payment_id": "pi_001",
            "customer_id": "cus_001",
            "amount": "5000",
            "currency": " INR ",
            "status": " SUCCEEDED "
        }
    ]

    result = clean_payments(records)

    assert len(result) == 1
    assert result[0]["payment_id"] == "pi_001"
    assert result[0]["amount"] == 5000
    assert result[0]["currency"] == "inr"
    assert result[0]["status"] == "succeeded"

