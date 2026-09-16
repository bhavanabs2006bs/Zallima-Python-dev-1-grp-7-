from config import STRIPE_API_KEY
import requests
from typing import Optional


STRIPE_API_URL = "https://api.stripe.com/v1/customers"


def fetch_stripe_customers(
    api_key: str,
    limit: int = 100,
    starting_after: Optional[str] = None
):
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    params = {
        "limit": limit
    }

    if starting_after:
        params["starting_after"] = starting_after

    response = requests.get(
        STRIPE_API_URL,
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    if not STRIPE_API_KEY:
        print("Stripe API key is not configured.")
    else:
        print("Stripe API key loaded successfully.")