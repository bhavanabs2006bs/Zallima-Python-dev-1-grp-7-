from datetime import datetime
from typing import Dict, Any, Optional, List

import stripe

from .base_extractor import BaseExtractor
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StripeExtractor(BaseExtractor):
    """Extract PaymentIntent records from Stripe."""

    def __init__(self, secret_key: str, **kwargs):
        super().__init__(
            api_key=secret_key,
            rate_limit_delay=0.1,
            **kwargs
        )

        self.secret_key = secret_key
        stripe.api_key = secret_key

    def authenticate(self) -> bool:
        """Verify that the Stripe API key works."""

        try:
            stripe.Account.retrieve()

            logger.info(
                "Stripe authentication successful"
            )

            return True

        except stripe.error.AuthenticationError:
            logger.error(
                "Stripe authentication failed: "
                "invalid API key"
            )

            return False

        except Exception as e:
            logger.error(
                f"Stripe authentication error: {e}"
            )

            return False

    def extract_page(
        self,
        cursor: Optional[str] = None,
        page_size: int = 100,
        since: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract one page of Stripe PaymentIntent records.

        If 'since' is provided, only PaymentIntents
        created after that timestamp are requested.
        """

        try:
            params = {
                "limit": min(page_size, 100)
            }

            # Pagination
            if cursor:
                params["starting_after"] = cursor

            # Incremental extraction
            if since:
                since_datetime = datetime.fromisoformat(
                    since.replace("Z", "+00:00")
                )

                params["created"] = {
                    "gte": int(
                        since_datetime.timestamp()
                    )
                }

                logger.info(
                    "Stripe incremental extraction "
                    f"since: {since}"
                )

            response = stripe.PaymentIntent.list(
                **params
            )

            records = []

            for payment_intent in response.data:

                records.append(
                    {
                        "id": payment_intent.id,
                        "customer": payment_intent.customer,
                        "amount": payment_intent.amount,
                        "currency": payment_intent.currency,
                        "status": payment_intent.status,
                        "description": payment_intent.description,
                        "created": payment_intent.created,
                        "metadata":(
                            payment_intent.metadata.to_dict()
                            if hasattr(payment_intent.metadata, "to_dict")
                            else dict(payment_intent.metadata)
                        )
                    }
                )

            next_cursor = None

            if response.has_more and response.data:
                next_cursor = response.data[-1].id

            logger.info(
                "Stripe page extracted: "
                f"{len(records)} records"
            )

            return {
                "records": records,
                "next_cursor": next_cursor,
                "total_count": len(records),
            }

        except stripe.error.StripeError as e:

            logger.error(
                f"Stripe API error: {e}"
            )

            raise

        except Exception as e:

            logger.error(
                "Unexpected Stripe extraction error: "
                f"{e}"
            )

            raise

    def extract_transactions(
        self,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract Stripe PaymentIntent records.

        When 'since' is provided, only records created
        after that datetime are requested.
        """

        logger.info(
            "Extracting Stripe transactions..."
        )

        since_value = None

        if since:
            since_value = since.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

        return self.extract_all(
            since=since_value
        )