from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

import requests

from .base_extractor import BaseExtractor
from ..utils.logger import get_logger


logger = get_logger(__name__)


class SalesforceExtractor(BaseExtractor):
    """Extract Contact records from Salesforce."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        **kwargs
    ):
        super().__init__(
            api_key=client_id,
            api_secret=client_secret,
            rate_limit_delay=0.1,
            **kwargs
        )

        self.client_id = client_id
        self.client_secret = client_secret

        self.access_token = None
        self.instance_url = None

    # ---------------------------------------------------------
    # AUTHENTICATION
    # ---------------------------------------------------------

    def authenticate(self) -> bool:
        """Authenticate with Salesforce using Client Credentials Flow."""

        logger.info(
            "Authenticating with Salesforce using "
            "Client Credentials Flow..."
        )

        try:
            auth_url = (
                "https://orgfarm-afea8b627a-dev-ed.develop.my.salesforce.com"
                "/services/oauth2/token"
            )

            response = requests.post(
                auth_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id.strip(),
                    "client_secret": self.client_secret.strip(),
                },
                timeout=30,
            )

            if response.status_code >= 400:
                logger.error(
                    f"Salesforce authentication failed: "
                    f"{response.status_code}"
                )
                logger.error(
                    f"Salesforce response: {response.text}"
                )

            response.raise_for_status()

            data = response.json()

            self.access_token = data["access_token"]
            self.instance_url = data.get("instance_url")

            if not self.instance_url:
                raise ValueError(
                    "Salesforce response did not contain instance_url"
                )

            logger.info(
                "Salesforce authentication successful"
            )

            return True

        except requests.RequestException as e:

            if getattr(e, "response", None) is not None:
                logger.error(
                    f"Salesforce authentication error: "
                    f"{e.response.text}"
                )
            else:
                logger.error(
                    f"Salesforce authentication error: {e}"
                )

            return False

        except KeyError as e:

            logger.error(
                "Salesforce authentication response "
                f"missing field: {e}"
            )

            return False

        except Exception as e:

            logger.error(
                f"Salesforce authentication error: {e}"
            )

            return False

    # ---------------------------------------------------------
    # EXTRACT ONE PAGE
    # ---------------------------------------------------------

    def extract_page(
        self,
        cursor: Optional[str] = None,
        page_size: int = 100,
        since: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract one page of Salesforce Contact records.

        If since is provided, only records modified after
        that timestamp are extracted.
        """

        if not self.access_token or not self.instance_url:
            raise RuntimeError(
                "Salesforce is not authenticated. "
                "Call authenticate() first."
            )

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:

            # -------------------------------------------------
            # PAGINATION
            # -------------------------------------------------

            if cursor:

                url = self.instance_url + cursor

                response = requests.get(
                    url,
                    headers=headers,
                    timeout=30,
                )

            else:

                api_version = "v65.0"

                # ---------------------------------------------
                # BASE SOQL QUERY
                # ---------------------------------------------

                soql = (
                    "SELECT Id, Email, FirstName, LastName, "
                    "Phone, CreatedDate, LastModifiedDate "
                    "FROM Contact "
                )

                # ---------------------------------------------
                # INCREMENTAL EXTRACTION
                # ---------------------------------------------

                if since:

                    logger.info(
                        "Salesforce incremental extraction "
                        f"since: {since}"
                    )

                    # Make sure the datetime is Salesforce-compatible.
                    #
                    # Expected input:
                    # 2026-09-08T19:42:28Z
                    #
                    # Salesforce SOQL accepts:
                    # 2026-09-08T19:42:28Z

                    try:

                        since_datetime = datetime.fromisoformat(
                            since.replace("Z", "+00:00")
                        )

                        # Convert to UTC.
                        if since_datetime.tzinfo is None:
                            since_datetime = since_datetime.replace(
                                tzinfo=timezone.utc
                            )
                        else:
                            since_datetime = since_datetime.astimezone(
                                timezone.utc
                            )

                        since_value = since_datetime.strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        )

                    except ValueError:

                        raise ValueError(
                            "Invalid Salesforce since datetime: "
                            f"{since}"
                        )

                    soql += (
                        "WHERE LastModifiedDate > "
                        f"{since_value} "
                    )

                # ---------------------------------------------
                # ORDER + LIMIT
                # ---------------------------------------------

                soql += (
                    "ORDER BY CreatedDate ASC "
                    f"LIMIT {min(page_size, 2000)}"
                )

                logger.info(
                    f"Salesforce SOQL: {soql}"
                )

                response = requests.get(
                    f"{self.instance_url}/services/data/"
                    f"{api_version}/query",
                    headers=headers,
                    params={
                        "q": soql
                    },
                    timeout=30,
                )

            # -------------------------------------------------
            # ERROR HANDLING
            # -------------------------------------------------

            if response.status_code >= 400:

                logger.error(
                    "Salesforce API returned HTTP "
                    f"{response.status_code}"
                )

                logger.error(
                    "Salesforce response body: "
                    f"{response.text}"
                )

            response.raise_for_status()

            # -------------------------------------------------
            # RESPONSE
            # -------------------------------------------------

            data = response.json()

            records = data.get(
                "records",
                []
            )

            # -------------------------------------------------
            # SALESFORCE PAGINATION
            # -------------------------------------------------

            next_cursor = None

            if not data.get("done", True):

                next_cursor = data.get(
                    "nextRecordsUrl"
                )

            logger.info(
                "Salesforce page extracted: "
                f"{len(records)} records"
            )

            return {
                "records": records,
                "next_cursor": next_cursor,
                "total_count": len(records),
            }

        except requests.RequestException as e:

            logger.error(
                f"Salesforce API error: {e}"
            )

            if getattr(e, "response", None) is not None:

                logger.error(
                    "Salesforce response body: "
                    f"{e.response.text}"
                )

            raise

        except Exception as e:

            logger.error(
                "Unexpected Salesforce extraction error: "
                f"{e}"
            )

            raise

    # ---------------------------------------------------------
    # EXTRACT CONTACTS
    # ---------------------------------------------------------

    def extract_contacts(
        self,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract Salesforce Contact records.

        If since is provided, only records modified
        after that datetime are requested.
        """

        logger.info(
            "Extracting Salesforce contacts..."
        )

        since_value = None

        if since:

            # Convert the last successful ETL time to UTC.
            if since.tzinfo is None:

                since = since.replace(
                    tzinfo=timezone.utc
                )

            else:

                since = since.astimezone(
                    timezone.utc
                )

            since_value = since.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

        return self.extract_all(
            since=since_value
        )