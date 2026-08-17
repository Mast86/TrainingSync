"""CSV export for Garmin activity summaries."""

import csv
import json
from pathlib import Path
from typing import Any, Iterable


class ActivityCsvExporter:
    """Write activity summaries as a single, analysis-friendly CSV file."""

    def write(self, activities: Iterable[dict[str, Any]], output_path: Path) -> int:
        rows = [self._normalise(activity) for activity in activities]
        columns = self._columns(rows)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        return len(rows)

    def read(self, input_path: Path) -> list[dict[str, Any]]:
        """Read a previously exported CSV, or return an empty history."""
        if not input_path.exists():
            return []
        with input_path.open(encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    def merge(
        self, existing: Iterable[dict[str, Any]], incoming: Iterable[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Merge activity records by ID; newer Garmin data takes precedence."""
        activities: dict[str, dict[str, Any]] = {}
        for activity in [*existing, *incoming]:
            activity_id = activity.get("activityId")
            if activity_id in (None, ""):
                raise ValueError("Every Garmin activity must include activityId")
            activities[str(activity_id)] = activity
        return sorted(activities.values(), key=lambda item: item.get("startTimeLocal", ""))

    @staticmethod
    def _normalise(activity: dict[str, Any]) -> dict[str, Any]:
        """Keep scalar values native; encode nested Garmin values as JSON strings."""
        return {
            key: json.dumps(value, ensure_ascii=False, sort_keys=True)
            if isinstance(value, (dict, list))
            else value
            for key, value in activity.items()
        }

    @staticmethod
    def _columns(rows: list[dict[str, Any]]) -> list[str]:
        all_columns = {column for row in rows for column in row}
        preferred = ["activityId", "activityName", "startTimeLocal", "activityType"]
        return [column for column in preferred if column in all_columns] + sorted(
            all_columns - set(preferred)
        )
