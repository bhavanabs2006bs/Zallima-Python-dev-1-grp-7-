
from unittest.mock import patch, Mock

from src.salesforce_extractor import (
    fetch_salesforce_data,
    fetch_all_salesforce_data
)


def test_salesforce_pagination():
    mock_response = Mock()

    mock_response.json.return_value = {
        "records": [
            {
                "Id": "001",
                "Name": "Test Customer"
            }
        ],
        "done": False,
        "nextRecordsUrl": (
            "/services/data/v60.0/query/next/abc123"
        )
    }

    mock_response.raise_for_status.return_value = None

    with patch(
        "src.salesforce_extractor.requests.get"
    ) as mock_get:

        mock_get.return_value = mock_response

        result = fetch_salesforce_data(
            access_token="test_token",
            query="SELECT Id, Name FROM Account"
        )

        mock_get.assert_called_once()

        _, kwargs = mock_get.call_args

        assert kwargs["params"]["q"] == (
            "SELECT Id, Name FROM Account"
        )

        assert result["done"] is False

        assert result["nextRecordsUrl"] == (
            "/services/data/v60.0/query/next/abc123"
        )


def test_fetch_all_salesforce_data():
    first_response = Mock()

    first_response.json.return_value = {
        "records": [
            {
                "Id": "001",
                "Name": "Customer One"
            }
        ],
        "done": False,
        "nextRecordsUrl": (
            "/services/data/v60.0/query/next/page2"
        )
    }

    first_response.raise_for_status.return_value = None

    second_response = Mock()

    second_response.json.return_value = {
        "records": [
            {
                "Id": "002",
                "Name": "Customer Two"
            }
        ],
        "done": True
    }

    second_response.raise_for_status.return_value = None

    with patch(
        "src.salesforce_extractor.requests.get"
    ) as mock_get:

        mock_get.side_effect = [
            first_response,
            second_response
        ]

        result = fetch_all_salesforce_data(
            access_token="test_token",
            query="SELECT Id, Name FROM Account"
        )

        assert len(result) == 2

        assert result[0]["Id"] == "001"
        assert result[1]["Id"] == "002"

        assert mock_get.call_count == 2
