from unittest.mock import patch, Mock

from src.stripe_extractor import (
    fetch_stripe_customers,
    fetch_all_stripe_customers
)


def test_stripe_pagination():
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [
            {
                "id": "cus_001",
                "name": "Test Customer"
            }
        ],
        "has_more": True
    }
    mock_response.raise_for_status.return_value = None

    with patch("src.stripe_extractor.requests.get") as mock_get:
        mock_get.return_value = mock_response

        fetch_stripe_customers(
            api_key="test_key",
            limit=10,
            starting_after="cus_previous"
        )

        mock_get.assert_called_once()

        _, kwargs = mock_get.call_args

        assert kwargs["params"]["limit"] == 10
        assert kwargs["params"]["starting_after"] == "cus_previous"


def test_fetch_all_stripe_customers():
    first_response = Mock()
    first_response.json.return_value = {
        "data": [
            {
                "id": "cus_001",
                "name": "Customer One"
            }
        ],
        "has_more": True
    }
    first_response.raise_for_status.return_value = None

    second_response = Mock()
    second_response.json.return_value = {
        "data": [
            {
                "id": "cus_002",
                "name": "Customer Two"
            }
        ],
        "has_more": False
    }
    second_response.raise_for_status.return_value = None

    with patch("src.stripe_extractor.requests.get") as mock_get:
        mock_get.side_effect = [
            first_response,
            second_response
        ]

        result = fetch_all_stripe_customers(
            api_key="test_key",
            limit=1
        )

        assert len(result) == 2
        assert result[0]["id"] == "cus_001"
        assert result[1]["id"] == "cus_002"
        assert mock_get.call_count == 2


def test_stripe_rate_limit_retry():
    rate_limit_response = Mock()
    rate_limit_response.status_code = 429
    rate_limit_response.headers = {
        "Retry-After": "0"
    }
    rate_limit_response.raise_for_status.return_value = None

    success_response = Mock()
    success_response.status_code = 200
    success_response.json.return_value = {
        "data": [
            {
                "id": "cus_003",
                "name": "After Retry"
            }
        ],
        "has_more": False
    }
    success_response.raise_for_status.return_value = None

    with patch("src.stripe_extractor.requests.get") as mock_get:
        mock_get.side_effect = [
            rate_limit_response,
            success_response
        ]

        result = fetch_stripe_customers(
            api_key="test_key",
            limit=10
        )

        assert result["data"][0]["id"] == "cus_003"
        assert mock_get.call_count == 2


def test_stripe_server_error_retry():
    server_error_response = Mock()
    server_error_response.status_code = 503
    server_error_response.headers = {}

    success_response = Mock()
    success_response.status_code = 200
    success_response.json.return_value = {
        "data": [
            {
                "id": "cus_004",
                "name": "Server Retry"
            }
        ],
        "has_more": False
    }
    success_response.raise_for_status.return_value = None

    with patch("src.stripe_extractor.requests.get") as mock_get:
        mock_get.side_effect = [
            server_error_response,
            success_response
        ]

        result = fetch_stripe_customers(
            api_key="test_key",
            limit=10
        )

        assert result["data"][0]["id"] == "cus_004"
        assert mock_get.call_count == 2
