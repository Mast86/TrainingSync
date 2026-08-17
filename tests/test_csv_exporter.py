import csv

from training_sync.csv_exporter import ActivityCsvExporter


def test_write_preserves_values_and_serialises_nested_data(tmp_path):
    destination = tmp_path / "activities.csv"
    count = ActivityCsvExporter().write(
        [
            {
                "activityId": 12,
                "activityName": "Morning run",
                "activityType": {"typeKey": "running"},
                "distance": 5000.0,
            }
        ],
        destination,
    )

    with destination.open(newline="", encoding="utf-8") as file:
        row = next(csv.DictReader(file))

    assert count == 1
    assert row["activityId"] == "12"
    assert row["activityType"] == '{"typeKey": "running"}'


def test_merge_replaces_existing_activity_and_keeps_other_activities():
    exporter = ActivityCsvExporter()

    activities = exporter.merge(
        [
            {"activityId": "1", "activityName": "Old name", "startTimeLocal": "2026-01-01"},
            {"activityId": "2", "activityName": "Keep", "startTimeLocal": "2026-01-02"},
        ],
        [{"activityId": 1, "activityName": "New name", "startTimeLocal": "2026-01-01"}],
    )

    assert [activity["activityId"] for activity in activities] == [1, "2"]
    assert activities[0]["activityName"] == "New name"
