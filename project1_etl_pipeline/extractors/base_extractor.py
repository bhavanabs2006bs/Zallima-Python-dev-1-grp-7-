from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time

from tenacity import retry, stop_after_attempt, wait_exponential

from ..utils.logger import get_logger

logger = get_logger(__name__)


class BaseExtractor(ABC):

    def __init__(
        self,
        api_key: str,
        api_secret: Optional[str] = None,
        rate_limit_delay: float = 1.0
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limit_delay = rate_limit_delay

        logger.info(
            f"{self.__class__.__name__} initialized"
        )

    @abstractmethod
    def authenticate(self) -> bool:
        pass

    @abstractmethod
    def extract_page(
        self,
        cursor: Optional[str] = None,
        page_size: int = 100,
        since: Optional[str] = None
    ) -> Dict[str, Any]:
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=5
        )
    )
    def extract_all(
        self,
        max_pages: int = 10,
        since: Optional[str] = None
    ) -> List[Dict[str, Any]]:

        all_records = []
        cursor = None
        page_count = 0

        logger.info(
            f"Starting extraction from "
            f"{self.__class__.__name__}"
        )

        if since:
            logger.info(
                f"Incremental extraction enabled. "
                f"Fetching records since: {since}"
            )
        else:
            logger.info(
                "Full extraction enabled."
            )

        while page_count < max_pages:

            time.sleep(self.rate_limit_delay)

            result = self.extract_page(
                cursor=cursor,
                since=since
            )

            records = result.get(
                "records",
                []
            )

            cursor = result.get(
                "next_cursor"
            )

            all_records.extend(records)

            page_count += 1

            logger.info(
                f"Page {page_count}: "
                f"Extracted {len(records)} records "
                f"(Total: {len(all_records)})"
            )

            if not cursor or len(records) == 0:
                break

        logger.info(
            f"Extraction complete: "
            f"{len(all_records)} total records"
        )

        return all_records