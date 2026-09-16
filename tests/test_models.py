from src.models import Customer, Payment


def test_customer_model():
    customer = Customer(
        id="cus_123",
        name="Bhavana",
        email="bhavana@example.com"
    )

    assert customer.id == "cus_123"
    assert customer.name == "Bhavana"


def test_payment_model():
    payment = Payment(
        id="pi_123",
        customer_id="cus_123",
        amount=500.0,
        currency="inr",
        status="succeeded"
    )

    assert payment.id == "pi_123"
    assert payment.amount == 500.0