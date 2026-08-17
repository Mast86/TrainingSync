from datetime import date

import training_sync.sync as sync
from training_sync.csv_exporter import ActivityCsvExporter


class FakeGarminClient:
    def __init__(self, token_path, page_size):
        self.token_path = token_path
        self.page_size = page_size

    def get_activities_between(self, start_date, end_date):
        assert (start_date, end_date) == (date(2026, 8, 1), date(2026, 8, 31))
        return [
            {"activityId": 1, "activityName": "Updated", "startTimeLocal": "2026-08-02"},
            {"activityId": 2, "activityName": "New", "startTimeLocal": "2026-08-03"},
        ]


def test_sync_merges_selected_period_into_annual_file(tmp_path, monkeypatch):
    monkeypatch.setattr(sync, "GarminActivityClient", FakeGarminClient)
    destination = tmp_path / "garmin_activities_2026.csv"
    ActivityCsvExporter().write(
        [{"activityId": 1, "activityName": "Original", "startTimeLocal": "2026-08-02"}],
        destination,
    )

    results = sync.sync_activity_history(
        tmp_path / "tokens", tmp_path, 100, date(2026, 8, 1), date(2026, 8, 31)
    )

    rows = ActivityCsvExporter().read(destination)
    assert results[2026].downloaded == 2
    assert results[2026].stored == 2
    assert {row["activityName"] for row in rows} == {"Updated", "New"}


def test_incremental_start_revisits_seven_days_from_latest_activity(tmp_path):
    destination = tmp_path / "garmin_activities_2026.csv"
    ActivityCsvExporter().write(
        [{"activityId": 1, "startTimeLocal": "2026-08-17 08:00:00"}], destination
    )

    start = sync._incremental_start(ActivityCsvExporter(), tmp_path, date(2026, 8, 20))

    assert start == date(2026, 8, 10)
