from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import DATABASE_URL
from src.loaders.customer_loader import (
    PaymentTable,
    load_payment
)


def test_load_payment_insert_and_update():

    first_payment = {
        "id": "pi_test_001",
        "customer_id": "cus_test_001",
        "amount": 5000,
        "currency": "inr",
        "status": "succeeded"
    }

    updated_payment = {
        "id": "pi_test_001",
        "customer_id": "cus_test_001",
        "amount": 7500,
        "currency": "inr",
        "status": "refunded"
    }

    load_payment(first_payment)

    load_payment(updated_payment)

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        payment = session.get(
            PaymentTable,
            "pi_test_001"
        )

        assert payment is not None
        assert payment.customer_id == "cus_test_001"
        assert payment.amount == 7500
        assert payment.currency == "inr"
        assert payment.status == "refunded"

    finally:
        session.close()