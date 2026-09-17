from src.transformers.customer_transformer import transform_customer


def test_transform_stripe_customer():
    stripe_data = {
        "id": "cus_123",
        "name": "Bhavana",
        "email": "bhavana@example.com"
    }

    result = transform_customer(stripe_data, "stripe")

    assert result["source"] == "stripe"
    assert result["customer_id"] == "cus_123"
    assert result["name"] == "Bhavana"


def test_transform_salesforce_customer():
    salesforce_data = {
        "Id": "001",
        "Name": "Test Customer",
        "Email": "test@example.com"
    }

    result = transform_customer(
        salesforce_data,
        "salesforce"
    )

    assert result["source"] == "salesforce"
    assert result["customer_id"] == "001"
    assert result["name"] == "Test Customer"
from src.transformers.payment_transformer import transform_payment


def test_transform_stripe_payment():
    stripe_data = {
        "id": "pi_123",
        "customer": "cus_123",
        "amount": 5000,
        "currency": "inr",
        "status": "succeeded"
    }

    result = transform_payment(
        stripe_data,
        "stripe"
    )

    assert result["source"] == "stripe"
    assert result["payment_id"] == "pi_123"
    assert result["customer_id"] == "cus_123"
    assert result["amount"] == 5000
    assert result["currency"] == "inr"
    assert result["status"] == "succeeded"    