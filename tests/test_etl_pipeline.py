
from unittest.mock import patch

from src.pipeline.etl_pipeline import (
    process_customers,
    process_payments
)


def test_process_stripe_customers():
    stripe_data = {
        "data": [
            {
                "id": "cus_etl_001",
                "name": "ETL Customer",
                "email": "etl@example.com"
            }
        ]
    }

    with patch(
        "src.pipeline.etl_pipeline.load_customer"
    ) as mock_load:

        result = process_customers(
            stripe_data,
            "stripe"
        )

        assert result == 1

        mock_load.assert_called_once_with({
            "id": "cus_etl_001",
            "name": "ETL Customer",
            "email": "etl@example.com"
        })


def test_process_salesforce_customers():
    salesforce_data = {
        "records": [
            {
                "Id": "001",
                "Name": "Salesforce Customer",
                "Email": "salesforce@example.com"
            }
        ]
    }

    with patch(
        "src.pipeline.etl_pipeline.load_customer"
    ) as mock_load:

        result = process_customers(
            salesforce_data,
            "salesforce"
        )

        assert result == 1

        mock_load.assert_called_once_with({
            "id": "001",
            "name": "Salesforce Customer",
            "email": "salesforce@example.com"
        })


def test_process_stripe_payments():
    stripe_data = {
        "data": [
            {
                "id": "pi_etl_001",
                "customer": "cus_etl_001",
                "amount": 5000,
                "currency": "inr",
                "status": "succeeded"
            }
        ]
    }

    with patch(
        "src.pipeline.etl_pipeline.load_payment"
    ) as mock_load:

        result = process_payments(
            stripe_data,
            "stripe"
        )

        assert result == 1

        mock_load.assert_called_once_with({
            "id": "pi_etl_001",
            "customer_id": "cus_etl_001",
            "amount": 5000,
            "currency": "inr",
            "status": "succeeded"
        })


def test_cleaning_before_etl():
    from src.transformers.cleaning import clean_customers

    raw_data = [
        {
            "customer_id": "cus_e2e_001",
            "name": "  ETL Customer  ",
            "email": " ETL@EXAMPLE.COM "
        },
        {
            "customer_id": "cus_e2e_001",
            "name": "Duplicate Customer",
            "email": "duplicate@example.com"
        }
    ]

    cleaned_data = clean_customers(raw_data)

    assert len(cleaned_data) == 1
    assert cleaned_data[0]["customer_id"] == "cus_e2e_001"
    assert cleaned_data[0]["name"] == "ETL Customer"
    assert cleaned_data[0]["email"] == "etl@example.com"

