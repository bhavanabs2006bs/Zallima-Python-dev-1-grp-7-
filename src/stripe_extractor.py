import requests
import time
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config import STRIPE_API_KEY
from src.utils.logger import get_logger
from src.utils.raw_storage import save_raw_json

logger = get_logger("stripe_extractor")

STRIPE_API_URL = "https://api.stripe.com/v1/customers"


class StripeRetryableError(Exception):
    """Raised when Stripe returns a temporary/retryable error."""


@retry(
    retry=retry_if_exception_type(StripeRetryableError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def fetch_stripe_customers(
    api_key: str,
    limit: int = 100,
    starting_after: Optional[str] = None
):
    """
    Fetch one page of customers from Stripe.

    Retries temporary errors such as:
    - HTTP 429 rate limiting
    - HTTP 5xx server errors
    """

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    params = {
        "limit": limit
    }

    if starting_after:
        params["starting_after"] = starting_after

    try:
        response = requests.get(
            STRIPE_API_URL,
            headers=headers,
            params=params,
            timeout=30
        )

        # Rate limit
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")

            if retry_after:
                try:
                    wait_seconds = float(retry_after)
                    logger.warning(
                        "Stripe rate limit reached. "
                        "Retrying after %s seconds.",
                        wait_seconds
                    )
                    time.sleep(wait_seconds)
                except ValueError:
                    logger.warning(
                        "Invalid Retry-After header received from Stripe."
                    )
            else:
                logger.warning(
                    "Stripe rate limit reached. Retrying..."
                )

            raise StripeRetryableError("Stripe rate limit exceeded.")

        # Temporary Stripe server errors
        if response.status_code in (500, 502, 503, 504):
            logger.warning(
                "Stripe temporary server error: HTTP %s. Retrying...",
                response.status_code
            )
            raise StripeRetryableError(
                f"Stripe temporary error: {response.status_code}"
            )

        # Other HTTP errors
        response.raise_for_status()

        data = response.json()

        logger.info(
            "Stripe customer page fetched successfully."
        )

        save_raw_json(data, "stripe_customers")

        return data

    except requests.RequestException as error:
        logger.error(
            "Stripe API request failed: %s",
            error
        )
        raise


def fetch_all_stripe_customers(
    api_key: str,
    limit: int = 100
):
    """
    Fetch all Stripe customers using cursor pagination.
    """

    all_customers = []
    starting_after = None

    while True:

        data = fetch_stripe_customers(
            api_key=api_key,
            limit=limit,
            starting_after=starting_after
        )

        customers = data.get("data", [])

        all_customers.extend(customers)

        if not data.get("has_more"):
            break

        if not customers:
            break

        starting_after = customers[-1]["id"]

    logger.info(
        "Finished Stripe pagination. Total customers: %s",
        len(all_customers)
    )

    return all_customers


if __name__ == "__main__":

    if not STRIPE_API_KEY:
        print("Stripe API key is not configured.")
    else:
        customers = fetch_all_stripe_customers(
            STRIPE_API_KEY
        )

        print(
            f"Total customers fetched: {len(customers)}"
        )