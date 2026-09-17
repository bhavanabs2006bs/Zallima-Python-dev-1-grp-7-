
from unittest.mock import patch, Mock

from src.utils.raw_storage import (
    save_raw_json,
    upload_raw_json_to_s3
)


def test_save_raw_json():
    test_data = {
        "id": "test_001",
        "name": "Test Customer"
    }

    file_path = save_raw_json(
        test_data,
        "test"
    )

    assert file_path.exists()

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        content = file.read()

    assert "test_001" in content
    assert "Test Customer" in content

    file_path.unlink()


@patch("src.utils.raw_storage.boto3.client")
def test_upload_raw_json_to_s3(mock_boto_client):

    mock_s3 = Mock()
    mock_boto_client.return_value = mock_s3

    test_data = {
        "id": "test_002",
        "name": "S3 Test Customer"
    }

    with patch(
        "src.utils.raw_storage.AWS_ACCESS_KEY_ID",
        "test_access_key"
    ), patch(
        "src.utils.raw_storage.AWS_SECRET_ACCESS_KEY",
        "test_secret_key"
    ), patch(
        "src.utils.raw_storage.AWS_S3_BUCKET",
        "test-bucket"
    ):

        result = upload_raw_json_to_s3(
            test_data,
            "test"
        )

    assert result.startswith("raw/test/")
    assert result.endswith(".json")

    mock_s3.put_object.assert_called_once()

    call_kwargs = (
        mock_s3.put_object.call_args.kwargs
    )

    assert call_kwargs["Bucket"] == "test-bucket"
    assert call_kwargs["ContentType"] == "application/json"
