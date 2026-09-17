
from src.transformers.customer_transformer import transform_customer
from src.validators.customer_validator import validate_customer

from src.transformers.payment_transformer import transform_payment
from src.validators.payment_validator import validate_payment

from src.transformers.cleaning import (
    clean_customers,
    clean_payments
)

from src.loaders.customer_loader import (
    load_customer,
    load_payment
)


def process_customers(data: dict, source: str):
    """
    Process customer data through the ETL flow:

    Extract → Transform → Clean → Validate → Load
    """

    records = []

    if source == "stripe":
        records = data.get("data", [])

    elif source == "salesforce":
        records = data.get("records", [])

    else:
        raise ValueError(
            f"Unsupported source: {source}"
        )

    # Transform source-specific records
    transformed_records = [
        transform_customer(record, source)
        for record in records
    ]

    # Clean transformed records
    cleaned_records = clean_customers(
        transformed_records
    )

    loaded_count = 0

    for record in cleaned_records:

        validated = validate_customer(
            record
        )

        load_customer({
            "id": validated.id,
            "name": validated.name,
            "email": validated.email
        })

        loaded_count += 1

    return loaded_count


def process_payments(data: dict, source: str):
    """
    Process payment data through the ETL flow:

    Extract → Transform → Clean → Validate → Load
    """

    records = []

    if source == "stripe":
        records = data.get("data", [])

    elif source == "salesforce":
        records = data.get("records", [])

    else:
        raise ValueError(
            f"Unsupported source: {source}"
        )

    # Transform source-specific records
    transformed_records = [
        transform_payment(record, source)
        for record in records
    ]

    # Clean transformed records
    cleaned_records = clean_payments(
        transformed_records
    )

    loaded_count = 0

    for record in cleaned_records:

        validated = validate_payment(
            record
        )

        load_payment({
            "id": validated.id,
            "customer_id": validated.customer_id,
            "amount": validated.amount,
            "currency": validated.currency,
            "status": validated.status
        })

        loaded_count += 1

    return loaded_count

