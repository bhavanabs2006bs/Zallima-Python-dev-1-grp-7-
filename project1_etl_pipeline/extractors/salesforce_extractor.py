import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from .base_extractor import BaseExtractor
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SalesforceExtractor(BaseExtractor):
    def __init__(self, client_id: str, client_secret: str, **kwargs):
        super().__init__(api_key=client_id, api_secret=client_secret, rate_limit_delay=0.1, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None

    def authenticate(self) -> bool:
        logger.info("Authenticating with Salesforce...")
        self.access_token = "mock_access_token_" + self.client_id[:10]
        logger.info("Salesforce authentication successful")
        return True

    def extract_page(self, cursor: Optional[str] = None, page_size: int = 100) -> Dict[str, Any]:
        records = [self._generate_mock_contact() for _ in range(min(page_size, random.randint(10, 50)))]
        has_more = random.random() > 0.7
        next_cursor = f"cursor_{len(records)}" if has_more else None
        return {"records": records, "next_cursor": next_cursor, "total_count": len(records)}

    def _generate_mock_contact(self) -> Dict[str, Any]:
        first_names = ["John", "Jane", "Mike", "Sarah", "David", "Emily", "Chris", "Anna"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller"]
        companies = ["Acme Corp", "Tech Solutions", "Global Industries", "StartupXYZ", "DataFlow Inc"]
        now = datetime.now()
        created_days_ago = random.randint(1, 365)
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        return {
            "Id": f"SF{random.randint(100000, 999999)}",
            "Email": f"{fn.lower()}.{ln.lower()}@example.com",
            "FirstName": fn,
            "LastName": ln,
            "Company": random.choice(companies),
            "Phone": f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "CreatedDate": (now - timedelta(days=created_days_ago)).isoformat(),
            "LastModifiedDate": (now - timedelta(days=random.randint(0, created_days_ago))).isoformat()
        }

    def extract_contacts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        logger.info("Extracting Salesforce contacts...")
        return self.extract_all()
