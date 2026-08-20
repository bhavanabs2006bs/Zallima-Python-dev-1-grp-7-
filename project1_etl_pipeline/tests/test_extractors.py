import pytest
from ..extractors import SalesforceExtractor, StripeExtractor


class TestSalesforceExtractor:
    def setup_method(self):
        self.extractor = SalesforceExtractor("test_id", "test_secret")

    def test_authenticate(self):
        assert self.extractor.authenticate() is True

    def test_extract_page(self):
        result = self.extractor.extract_page(page_size=10)
        assert "records" in result
        assert len(result["records"]) <= 10

    def test_extract_all(self):
        records = self.extractor.extract_all(max_pages=2)
        assert len(records) > 0
        assert "Id" in records[0]


class TestStripeExtractor:
    def setup_method(self):
        self.extractor = StripeExtractor("sk_test")

    def test_authenticate(self):
        assert self.extractor.authenticate() is True

    def test_extract_page(self):
        result = self.extractor.extract_page(page_size=10)
        assert "records" in result

    def test_extract_all(self):
        records = self.extractor.extract_all(max_pages=2)
        assert len(records) > 0
        assert "id" in records[0]
