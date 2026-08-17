"""Command-line interface for the Garmin activity-history synchronisation."""

import argparse
from datetime import date
from pathlib import Path

from .config import DEFAULT_OUTPUT_DIRECTORY, DEFAULT_PAGE_SIZE, DEFAULT_TOKEN_PATH
from .sync import sync_activity_history


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronise Garmin Connect activities into annual CSV files."
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--year", type=int, help="Calendar year to synchronise.")
    selection.add_argument("--all-years", action="store_true", help="Download all history.")
    parser.add_argument("--month", type=int, choices=range(1, 13), metavar="1-12")
    parser.add_argument("--from", dest="start_date", type=_parse_date, metavar="YYYY-MM-DD")
    parser.add_argument("--to", dest="end_date", type=_parse_date, metavar="YYYY-MM-DD")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    parser.add_argument("--tokens", type=Path, default=DEFAULT_TOKEN_PATH)
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    args = parser.parse_args()

    if args.month and not args.year:
        parser.error("--month requires --year")
    if bool(args.start_date) != bool(args.end_date):
        parser.error("--from and --to must be used together")
    if args.year and (args.start_date or args.end_date):
        parser.error("--year cannot be combined with --from/--to")
    if args.all_years and (args.start_date or args.end_date or args.month):
        parser.error("--all-years cannot be combined with another date selector")
    if args.page_size < 1:
        parser.error("--page-size must be positive")
    return args


def main() -> None:
    args = parse_args()
    start_date, end_date = _selected_dates(args)
    results = sync_activity_history(
        args.tokens,
        args.output_dir,
        args.page_size,
        start_date,
        end_date,
        args.all_years,
    )
    for year, result in sorted(results.items()):
        print(f"{year}: downloaded {result.downloaded}, stored {result.stored} -> {result.output_path}")


def _selected_dates(args: argparse.Namespace) -> tuple[date | None, date | None]:
    if args.start_date:
        return args.start_date, args.end_date
    if args.year:
        if args.month:
            start = date(args.year, args.month, 1)
            end = date(args.year + (args.month == 12), args.month % 12 + 1, 1)
            return start, end.fromordinal(end.toordinal() - 1)
        return date(args.year, 1, 1), date(args.year, 12, 31)
    return None, None


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("use YYYY-MM-DD") from error


if __name__ == "__main__":
    main()
