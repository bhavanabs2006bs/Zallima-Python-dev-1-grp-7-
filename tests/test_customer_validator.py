from src.validators.customer_validator import validate_customer


def test_validate_customer():
    data = {
        "customer_id": "cus_123",
        "name": "Bhavana",
        "email": "bhavana@example.com"
    }

    customer = validate_customer(data)

    assert customer.id == "cus_123"
    assert customer.name == "Bhavana"
    assert customer.email == "bhavana@example.com"
from src.validators.payment_validator import validate_payment


def test_validate_payment():
    data = {
        "payment_id": "pi_123",
        "customer_id": "cus_123",
        "amount": 5000,
        "currency": "inr",
        "status": "succeeded"
    }

    payment = validate_payment(data)

    assert payment.id == "pi_123"
    assert payment.customer_id == "cus_123"
    assert payment.amount == 5000
    assert payment.currency == "inr"
    assert payment.status == "succeeded"    