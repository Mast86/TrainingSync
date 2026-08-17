"""Use case for incrementally synchronising Garmin activities to annual CSVs."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .csv_exporter import ActivityCsvExporter
from .config import DEFAULT_LOOKBACK_DAYS
from .garmin_client import GarminActivityClient


@dataclass(frozen=True)
class YearSyncResult:
    """Outcome for one annual CSV file."""

    downloaded: int
    stored: int
    output_path: Path


def sync_activity_history(
    token_path: Path,
    output_directory: Path,
    page_size: int,
    start_date: date | None = None,
    end_date: date | None = None,
    all_years: bool = False,
) -> dict[int, YearSyncResult]:
    """Synchronise a date range into annual CSV files, merging by activity ID.

    With no dates, the current annual CSV is updated incrementally, revisiting
    the preceding seven days for recently edited Garmin activities. ``all_years``
    is intended for the first full import and downloads Garmin's entire history.
    """
    if all_years and (start_date or end_date):
        raise ValueError("all_years cannot be combined with a date range")

    exporter = ActivityCsvExporter()
    today = date.today()
    if not all_years and start_date is None and end_date is None:
        start_date = _incremental_start(exporter, output_directory, today)
    start_date = start_date or date(today.year, 1, 1)
    end_date = end_date or today
    if end_date < start_date:
        raise ValueError("end_date must not be before start_date")

    client = GarminActivityClient(token_path, page_size)
    activities_by_year: dict[int, list[dict[str, Any]]] = defaultdict(list)

    if all_years:
        for activity in client.get_all_activities():
            activities_by_year[_activity_year(activity)].append(activity)
    else:
        for year, year_start, year_end in _calendar_year_ranges(start_date, end_date):
            activities_by_year[year].extend(
                client.get_activities_between(year_start, year_end)
            )

    results: dict[int, YearSyncResult] = {}
    for year, downloaded in activities_by_year.items():
        output_path = output_directory / f"garmin_activities_{year}.csv"
        merged = exporter.merge(exporter.read(output_path), downloaded)
        stored = exporter.write(merged, output_path)
        results[year] = YearSyncResult(len(downloaded), stored, output_path)
    return results


def _calendar_year_ranges(start_date: date, end_date: date):
    for year in range(start_date.year, end_date.year + 1):
        yield (
            year,
            max(start_date, date(year, 1, 1)),
            min(end_date, date(year, 12, 31)),
        )


def _activity_year(activity: dict[str, Any]) -> int:
    """Use Garmin's local activity timestamp to select the annual CSV."""
    return date.fromisoformat(str(activity["startTimeLocal"])[:10]).year


def _incremental_start(
    exporter: ActivityCsvExporter, output_directory: Path, today: date
) -> date:
    """Resume from the latest stored activity, with a short safety overlap."""
    output_path = output_directory / f"garmin_activities_{today.year}.csv"
    activity_dates = []
    for activity in exporter.read(output_path):
        try:
            activity_dates.append(date.fromisoformat(activity["startTimeLocal"][:10]))
        except (KeyError, TypeError, ValueError):
            continue
    if not activity_dates:
        return date(today.year, 1, 1)
    return max(date(today.year, 1, 1), max(activity_dates) - timedelta(days=DEFAULT_LOOKBACK_DAYS))
