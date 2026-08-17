# TrainingSync

A read-only Python utility for synchronising Garmin Connect activities to CSV
files. The package does not analyse workouts or make recommendations: it only
produces a local history that can be reused later.

> The connection uses the unofficial
> [`garminconnect`](https://github.com/cyberjunky/python-garminconnect) library.
> Garmin may change its web services; passwords and tokens must be treated as
> secrets.

## Installation

Requires Python 3.12 or later. From the project directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

The first command creates the local `.venv` virtual environment; the last one
installs the project in editable mode inside that environment.

## Synchronisation interface

The command is:

```powershell
python -m training_sync [options]
```

On the first run, you will be prompted for Garmin email, password and, when
needed, an MFA code. Session tokens are stored in `garmin_tokens/` and are not
included in Git. They are reused on later runs.

Without date selectors, an incremental synchronisation of the current year is
performed: the program starts from the date of the latest activity already
stored in the relevant CSV and downloads the previous seven days again. This
small overlap captures recent changes made in Garmin without downloading the
entire year. If the current year's CSV does not exist, the current year is
downloaded from its beginning:

```powershell
python -m training_sync
```

Activities are stored in one CSV per year, for example:

```text
data/
  garmin_activities_2024.csv
  garmin_activities_2025.csv
  garmin_activities_2026.csv
```

Each run downloads only the requested interval. For every affected year, the
program reads the existing CSV, if present, and merges activities by
`activityId`: freshly downloaded records replace records with the same ID, while
all other activities are retained. The full history is therefore not downloaded
again during normal use. To download an entire year again, explicitly use
`--year`.

### Select a period

```powershell
# A full year
python -m training_sync --year 2025

# A month in a year
python -m training_sync --year 2026 --month 8

# An explicit, inclusive date range
python -m training_sync --from 2025-12-15 --to 2026-01-15

# Initial import or full rebuild: download all history
python -m training_sync --all-years
```

`--month` requires `--year`. `--from` and `--to` must always be specified
together. `--all-years` cannot be combined with any other date selector. A date
range that crosses New Year's Day updates both relevant annual CSV files.

### Paths and automation

Default values are defined in `training_sync/config.py`. Override them without
changing code:

```powershell
python -m training_sync --year 2026 `
  --tokens D:\Private\garmin-tokens `
  --output-dir D:\Training\garmin-csv
```

For unattended runs, set `GARMIN_EMAIL` and `GARMIN_PASSWORD`. If either is not
defined, it is requested interactively. Avoid storing your password in a
long-lived environment variable.

Each CSV row represents a Garmin activity summary. Scalar fields are retained
as columns; objects and lists returned by the Garmin API are retained as JSON
text in the relevant CSV cell.

## Python API

The same functionality can be called from Python:

```python
from datetime import date
from pathlib import Path

from training_sync.sync import sync_activity_history

results = sync_activity_history(
    token_path=Path("garmin_tokens"),
    output_directory=Path("data"),
    page_size=100,
    start_date=date(2026, 8, 1),
    end_date=date(2026, 8, 31),
)
```

`results` is a dictionary indexed by year. Each value reports the number of
downloaded activities, the total number stored in that annual CSV, and the
path of the resulting file. For a full import, use `all_years=True` and do not
pass dates.

## Tests

```powershell
pip install -e ".[test]"
python -m pytest
```
