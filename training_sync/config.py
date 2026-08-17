"""Default paths and settings for the synchronisation program.

Change these values to customise the standard source and destination locations.
They can also be overridden with command-line options.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIRECTORY = PROJECT_ROOT / "data"
DEFAULT_TOKEN_PATH = PROJECT_ROOT / "garmin_tokens"
DEFAULT_PAGE_SIZE = 100
DEFAULT_LOOKBACK_DAYS = 7
