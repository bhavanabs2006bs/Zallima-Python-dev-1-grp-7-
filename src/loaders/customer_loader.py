
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Float,
    DateTime
)
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import DATABASE_URL


Base = declarative_base()


class CustomerTable(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class PaymentTable(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True)
    customer_id = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    status = Column(String, nullable=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


def get_database_session():
    """
    Create a PostgreSQL database session.
    """

    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL is not configured."
        )

    engine = create_engine(DATABASE_URL)

    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)

    return Session()


def load_customer(customer):
    """
    Insert or update a customer.

    Existing records are updated instead of duplicated.
    """

    session = get_database_session()

    try:

        existing_customer = session.get(
            CustomerTable,
            customer["id"]
        )

        if existing_customer:

            existing_customer.name = customer.get("name")
            existing_customer.email = customer.get("email")

        else:

            new_customer = CustomerTable(
                id=customer["id"],
                name=customer.get("name"),
                email=customer.get("email")
            )

            session.add(new_customer)

        session.commit()

    except Exception:

        session.rollback()
        raise

    finally:

        session.close()


def load_payment(payment):
    """
    Insert or update a payment.

    Existing records are updated instead of duplicated.
    """

    session = get_database_session()

    try:

        existing_payment = session.get(
            PaymentTable,
            payment["id"]
        )

        if existing_payment:

            existing_payment.customer_id = (
                payment.get("customer_id")
            )

            existing_payment.amount = (
                payment.get("amount")
            )

            existing_payment.currency = (
                payment.get("currency")
            )

            existing_payment.status = (
                payment.get("status")
            )

        else:

            new_payment = PaymentTable(
                id=payment["id"],
                customer_id=payment.get("customer_id"),
                amount=payment.get("amount"),
                currency=payment.get("currency"),
                status=payment.get("status")
            )

            session.add(new_payment)

        session.commit()

    except Exception:

        session.rollback()
        raise

    finally:

        session.close()

