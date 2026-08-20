import pytest
from datetime import datetime
from ..transformers import DataTransformer


class TestDataTransformer:
    def setup_method(self):
        self.transformer = DataTransformer()

    def test_transform_salesforce(self):
        raw = [{"Id": "SF123", "Email": "t@t.com", "FirstName": "T", "LastName": "U",
                "Company": "Corp", "CreatedDate": "2024-01-01T00:00:00", "LastModifiedDate": "2024-01-01T00:00:00"}]
        result = self.transformer.transform_salesforce(raw)
        assert result.success is True
        assert result.records_processed == 1

    def test_transform_stripe(self):
        raw = [{"id": "pi_123", "customer": "cus_1", "amount": 5000, "currency": "usd",
                "status": "succeeded", "created": 1704067200}]
        result = self.transformer.transform_stripe(raw)
        assert result.success is True
        assert result.records_processed == 1
