import requests
from typing import Optional

from src.config import SALESFORCE_ACCESS_TOKEN
from src.utils.logger import get_logger
from src.utils.raw_storage import save_raw_json

logger = get_logger("salesforce_extractor")

SALESFORCE_API_URL = (
    "https://your-domain.my.salesforce.com/services/data/v60.0/query"
)


def fetch_salesforce_data(
    access_token: str,
    query: str,
    next_url: Optional[str] = None
):
    """
    Fetch one page of data from Salesforce.

    Supports Salesforce pagination using nextRecordsUrl.
    """

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    if next_url:
        url = next_url
        params = None
    else:
        url = SALESFORCE_API_URL
        params = {"q": query}

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        logger.info(
            "Salesforce data page fetched successfully."
        )

        save_raw_json(data, "salesforce")

        return data

    except requests.RequestException as error:
        logger.error(
            "Salesforce API request failed: %s",
            error
        )
        raise


def fetch_all_salesforce_data(
    access_token: str,
    query: str
):
    """
    Fetch all Salesforce records using nextRecordsUrl pagination.
    """

    all_records = []
    next_url = None

    while True:

        data = fetch_salesforce_data(
            access_token=access_token,
            query=query,
            next_url=next_url
        )

        records = data.get("records", [])

        all_records.extend(records)

        # Salesforce returns done=True on the final page.
        if data.get("done"):
            break

        # Get the next page URL.
        next_url = data.get("nextRecordsUrl")

        # Safety check to avoid an infinite loop.
        if not next_url:
            logger.warning(
                "Salesforce response has no nextRecordsUrl."
            )
            break

    logger.info(
        "Finished Salesforce pagination. Total records: %s",
        len(all_records)
    )

    return all_records


if __name__ == "__main__":

    if not SALESFORCE_ACCESS_TOKEN:
        print("Salesforce access token is not configured.")
    else:
        print(
            "Salesforce access token loaded successfully."
        )
