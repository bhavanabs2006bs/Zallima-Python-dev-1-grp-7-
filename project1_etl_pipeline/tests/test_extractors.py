from unittest.mock import Mock

import pytest
import requests

from ..extractors import SalesforceExtractor, StripeExtractor
from ..extractors import stripe_extractor as stripe_module
from ..extractors import salesforce_extractor as salesforce_module


def response(status=200, payload=None):
    r = Mock()
    r.status_code = status
    r.json.return_value = payload or {}

    if status >= 400:
        r.raise_for_status.side_effect = requests.HTTPError(
            f"HTTP {status}"
        )
    else:
        r.raise_for_status.side_effect = None

    return r


class TestSalesforceExtractor:

    def test_authenticate(self, monkeypatch):
        mock_response = response(
            200,
            {
                "access_token": "sf-test-token",
                "instance_url": "https://example.my.salesforce.com",
            },
        )

        monkeypatch.setattr(
            salesforce_module.requests,
            "post",
            Mock(return_value=mock_response),
        )

        extractor = SalesforceExtractor(
            client_id="client_id",
            client_secret="client_secret",
        )

        assert extractor.authenticate() is True
        assert extractor.access_token == "sf-test-token"
        assert (
            extractor.instance_url
            == "https://example.my.salesforce.com"
        )

    def test_extract_page(self, monkeypatch):
        mock_response = response(
            200,
            {
                "records": [
                    {
                        "Id": "SF1",
                        "Email": "a@example.com",
                        "FirstName": "John",
                        "LastName": "Doe",
                    }
                ],
                "done": True,
            },
        )

        monkeypatch.setattr(
            salesforce_module.requests,
            "get",
            Mock(return_value=mock_response),
        )

        extractor = SalesforceExtractor(
            client_id="client_id",
            client_secret="client_secret",
        )

        extractor.access_token = "sf-test-token"
        extractor.instance_url = (
            "https://example.my.salesforce.com"
        )

        result = extractor.extract_page()

        assert len(result["records"]) == 1
        assert result["records"][0]["Id"] == "SF1"
        assert result["next_cursor"] is None

    def test_extract_all_pagination(self, monkeypatch):
        mock_get = Mock(
            side_effect=[
                response(
                    200,
                    {
                        "records": [
                            {
                                "Id": "SF1",
                                "Email": "a@example.com",
                            }
                        ],
                        "done": False,
                        "nextRecordsUrl":
                            "/services/data/v65.0/query/next-1",
                    },
                ),
                response(
                    200,
                    {
                        "records": [
                            {
                                "Id": "SF2",
                                "Email": "b@example.com",
                            }
                        ],
                        "done": True,
                    },
                ),
            ]
        )

        monkeypatch.setattr(
            salesforce_module.requests,
            "get",
            mock_get,
        )

        extractor = SalesforceExtractor(
            client_id="client_id",
            client_secret="client_secret",
        )

        extractor.access_token = "sf-test-token"
        extractor.instance_url = (
            "https://example.my.salesforce.com"
        )

        records = extractor.extract_all(max_pages=2)

        assert len(records) == 2
        assert records[0]["Id"] == "SF1"
        assert records[1]["Id"] == "SF2"
        assert mock_get.call_count == 2


class TestStripeExtractor:

    def test_authenticate(self, monkeypatch):
        mock_retrieve = Mock(
            return_value={"id": "acct_test"}
        )

        monkeypatch.setattr(
            stripe_module.stripe.Account,
            "retrieve",
            mock_retrieve,
        )

        extractor = StripeExtractor(
            "sk_test_unit_test_key"
        )

        assert extractor.authenticate() is True
        mock_retrieve.assert_called_once()

    def test_extract_page(self, monkeypatch):
        mock_list = Mock(
            return_value=Mock(
                data=[
                    Mock(
                        id="pi_1",
                        customer="cus_1",
                        amount=1000,
                        currency="usd",
                        status="succeeded",
                        description="Test payment",
                        created=1700000000,
                        metadata={},
                    )
                ],
                has_more=False,
            )
        )

        monkeypatch.setattr(
            stripe_module.stripe.PaymentIntent,
            "list",
            mock_list,
        )

        extractor = StripeExtractor(
            "sk_test_unit_test_key"
        )

        result = extractor.extract_page()

        assert len(result["records"]) == 1
        assert result["records"][0]["id"] == "pi_1"
        assert result["records"][0]["amount"] == 1000
        assert result["next_cursor"] is None

    def test_extract_all_pagination(self, monkeypatch):
        first_page = Mock(
            data=[
                Mock(
                    id="pi_1",
                    customer="cus_1",
                    amount=1000,
                    currency="usd",
                    status="succeeded",
                    description="Payment 1",
                    created=1700000000,
                    metadata={},
                )
            ],
            has_more=True,
        )

        second_page = Mock(
            data=[
                Mock(
                    id="pi_2",
                    customer="cus_2",
                    amount=2000,
                    currency="usd",
                    status="succeeded",
                    description="Payment 2",
                    created=1700000100,
                    metadata={},
                )
            ],
            has_more=False,
        )

        mock_list = Mock(
            side_effect=[
                first_page,
                second_page,
            ]
        )

        monkeypatch.setattr(
            stripe_module.stripe.PaymentIntent,
            "list",
            mock_list,
        )

        extractor = StripeExtractor(
            "sk_test_unit_test_key"
        )

        records = extractor.extract_all(max_pages=2)

        assert len(records) == 2
        assert records[0]["id"] == "pi_1"
        assert records[1]["id"] == "pi_2"

        assert mock_list.call_args_list[1].kwargs[
            "starting_after"
        ] == "pi_1"