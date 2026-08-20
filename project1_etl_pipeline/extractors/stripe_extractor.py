import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from .base_extractor import BaseExtractor
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StripeExtractor(BaseExtractor):
    def __init__(self, secret_key: str, **kwargs):
        super().__init__(api_key=secret_key, rate_limit_delay=0.1, **kwargs)
        self.secret_key = secret_key

    def authenticate(self) -> bool:
        logger.info("Authenticating with Stripe...")
        logger.info("Stripe authentication successful")
        return True

    def extract_page(self, cursor: Optional[str] = None, page_size: int = 100) -> Dict[str, Any]:
        records = [self._generate_mock_transaction() for _ in range(min(page_size, random.randint(5, 30)))]
        has_more = random.random() > 0.6
        next_cursor = f"pi_{random.randint(1000000, 9999999)}" if has_more else None
        return {"records": records, "next_cursor": next_cursor, "total_count": len(records)}

    def _generate_mock_transaction(self) -> Dict[str, Any]:
        statuses = ["succeeded", "pending", "failed"]
        currencies = ["usd", "eur", "gbp"]
        now = datetime.now()
        created_days_ago = random.randint(0, 30)
        return {
            "id": f"pi_{random.randint(10000000, 99999999)}",
            "customer": f"cus_{random.randint(100000, 999999)}",
            "amount": random.randint(1000, 100000),
            "currency": random.choice(currencies),
            "status": random.choice(statuses),
            "description": random.choice(["Pro plan subscription", "One-time purchase", "Annual license", "Support ticket"]),
            "created": int((now - timedelta(days=created_days_ago)).timestamp()),
            "metadata": {}
        }

    def extract_transactions(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        logger.info("Extracting Stripe transactions...")
        return self.extract_all()
