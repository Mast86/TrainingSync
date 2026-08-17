"""Small adapter around the Garmin Connect client."""

import os
from datetime import date
from getpass import getpass
from pathlib import Path
from typing import Any

class GarminActivityClient:
    """Authenticate and retrieve all activity summary records."""

    def __init__(self, token_path: Path, page_size: int) -> None:
        self.token_path = token_path
        self.page_size = page_size
        self._api: Any | None = None

    def login(self) -> Any:
        """Use stored tokens when available, otherwise prompt for credentials."""
        if self._api is not None:
            return self._api
        try:
            from garminconnect import Garmin
        except ImportError as error:
            raise RuntimeError(
                "The Garmin client is not installed. Run: pip install -e ."
            ) from error
        api = Garmin()
        try:
            api.login(str(self.token_path))
            self._api = api
            return self._api
        except Exception:
            # A first run or an expired token requires a normal Garmin login.
            email = os.getenv("GARMIN_EMAIL") or input("Garmin email: ").strip()
            password = os.getenv("GARMIN_PASSWORD") or getpass("Garmin password: ")
            api = Garmin(
                email=email,
                password=password,
                prompt_mfa=lambda: input("Garmin MFA code: ").strip(),
            )
            api.login(str(self.token_path))
            self._api = api
            return self._api

    def get_activities_between(
        self, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """Fetch activity summaries in the inclusive Garmin date range."""
        return self.login().get_activities_by_date(
            start_date.isoformat(), end_date.isoformat()
        ) or []

    def get_all_activities(self) -> list[dict[str, Any]]:
        """Fetch the complete activity history using Garmin's paginated endpoint."""
        api = self.login()
        activities: list[dict[str, Any]] = []
        start = 0

        while True:
            page = api.get_activities(start, self.page_size) or []
            activities.extend(page)
            if len(page) < self.page_size:
                return activities
            start += self.page_size
