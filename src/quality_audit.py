"""Profile the raw Zomato snapshot before it enters the analytics pipeline.

The script intentionally uses only the Python standard library so it can run
locally and in Databricks-adjacent environments without a package install.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, median
from urllib.parse import urlsplit, urlunsplit


NUMERIC_COLUMNS = ("rate_clean", "cost_clean", "votes")
REQUIRED_COLUMNS = {
    "url",
    "name",
    "location",
    "cuisines",
    "rate_clean",
    "cost_clean",
    "votes",
    "online_order",
    "book_table",
}
YES_NO_COLUMNS = ("online_order", "book_table")

# Review text can be much larger than the csv module's default 128 KiB limit.
csv.field_size_limit(sys.maxsize)


def is_blank(value: str | None) -> bool:
    return value is None or value.strip().lower() in {"", "nan", "none", "null"}


def canonical_url(value: str) -> str:
    """Remove listing context so the same restaurant has a stable business key."""
    if is_blank(value):
        return ""
    parsed = urlsplit(value.strip())
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), "", ""))


def parse_number(value: str | None) -> float | None:
    if is_blank(value):
        return None
    try:
        return float(value.replace(",", "").strip())
    except ValueError:
        return None


def percentage(part: int, total: int) -> float:
    return round((part / total * 100), 2) if total else 0.0


def write_markdown(report: dict, output_path: Path) -> None:
    profile = report["profile"]
    missing = report["missingness"]
    checks = report["quality_checks"]
    lines = [
        "# Zomato Dataset Quality Report",
        "",
        "## Scope",
        "",
        "The source is a historical Zomato restaurant-listing snapshot. It has no date field, so it cannot support time-series growth or demand-forecasting claims.",
        "",
        "## Dataset And Grain",
        "",
        f"- Rows read: **{profile['row_count']:,}**",
        f"- Columns: **{profile['column_count']}**",
        "- Raw grain: one restaurant listing record, not necessarily one unique restaurant. Listing category and Zomato URL context can create repeat appearances.",
        f"- Distinct canonical restaurant URLs: **{profile['distinct_canonical_urls']:,}**",
        f"- Rows with a repeated canonical URL: **{checks['repeated_canonical_url_rows']:,}** ({checks['repeated_canonical_url_row_rate']}%)",
        "",
        "## High-Signal Checks",
        "",
        f"- Exact duplicate rows: **{checks['exact_duplicate_rows']:,}** ({checks['exact_duplicate_row_rate']}%)",
        f"- Ratings outside 1.0-5.0: **{checks['invalid_rating_rows']:,}**",
        f"- Costs less than or equal to zero: **{checks['invalid_cost_rows']:,}**",
        f"- Negative votes: **{checks['negative_vote_rows']:,}**",
        f"- Unexpected online-order values: **{checks['unexpected_online_order_values']:,}**",
        f"- Unexpected table-booking values: **{checks['unexpected_book_table_values']:,}**",
        "",
        "## Missingness",
        "",
        "| Field | Missing rows | Missing rate |",
        "| --- | ---: | ---: |",
    ]
    for column, values in sorted(missing.items(), key=lambda item: item[1]["missing_rows"], reverse=True):
        lines.append(f"| {column} | {values['missing_rows']:,} | {values['missing_rate']}% |")

    lines.extend(
        [
            "",
            "## Numeric Distribution",
            "",
            "| Field | Valid rows | Min | Median | Mean | Max |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for column, values in report["numeric_summary"].items():
        lines.append(
            f"| {column} | {values['valid_rows']:,} | {values['min']} | {values['median']} | {values['mean']} | {values['max']} |"
        )

    lines.extend(
        [
            "",
            "## Decision For The Pipeline",
            "",
            "1. Keep the raw listing table for listing-level analysis.",
            "2. Create a canonical restaurant key from the URL without its query string for distinct restaurant counts and ML train/test grouping.",
            "3. Do not drop every row with a null. Apply field-specific rules: ratings are required for rating analysis, while missing dish and review text should not remove a restaurant from market analysis.",
            "4. Use a cuisine bridge table because one restaurant can serve multiple cuisines.",
            "5. Treat votes as an engagement proxy and observed ratings as platform snapshot outcomes, not demand, revenue, or causal performance measures.",
            "",
            "The machine-readable version of this report is `reports/data_quality_summary.json`.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def audit(input_path: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    missing = Counter()
    service_values = {column: Counter() for column in YES_NO_COLUMNS}
    numeric_values = {column: [] for column in NUMERIC_COLUMNS}
    malformed_numeric = Counter()
    canonical_urls = Counter()
    row_hashes: set[str] = set()
    rows = 0
    exact_duplicates = 0

    with input_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = reader.fieldnames or []
        absent = REQUIRED_COLUMNS.difference(fieldnames)
        if absent:
            raise ValueError(f"Missing required columns: {', '.join(sorted(absent))}")

        for row in reader:
            rows += 1
            row_digest = hashlib.sha256(
                "\x1f".join(row.get(column, "") for column in fieldnames).encode("utf-8", errors="replace")
            ).hexdigest()
            if row_digest in row_hashes:
                exact_duplicates += 1
            else:
                row_hashes.add(row_digest)

            for column in fieldnames:
                if is_blank(row.get(column)):
                    missing[column] += 1

            key = canonical_url(row.get("url", ""))
            if key:
                canonical_urls[key] += 1

            for column in YES_NO_COLUMNS:
                value = (row.get(column) or "").strip().title()
                if not is_blank(value):
                    service_values[column][value] += 1

            for column in NUMERIC_COLUMNS:
                raw_value = row.get(column)
                parsed = parse_number(raw_value)
                if parsed is None:
                    if not is_blank(raw_value):
                        malformed_numeric[column] += 1
                    continue
                numeric_values[column].append(parsed)

    repeated_canonical_rows = sum(count for count in canonical_urls.values() if count > 1)
    unexpected_services = {
        column: sum(count for value, count in values.items() if value not in {"Yes", "No"})
        for column, values in service_values.items()
    }

    numeric_summary = {
        column: {
            "valid_rows": len(values),
            "min": round(min(values), 2) if values else None,
            "median": round(median(values), 2) if values else None,
            "mean": round(mean(values), 2) if values else None,
            "max": round(max(values), 2) if values else None,
        }
        for column, values in numeric_values.items()
    }
    report = {
        "source": str(input_path),
        "profile": {
            "row_count": rows,
            "column_count": len(fieldnames),
            "columns": fieldnames,
            "distinct_canonical_urls": len(canonical_urls),
        },
        "missingness": {
            column: {"missing_rows": missing[column], "missing_rate": percentage(missing[column], rows)}
            for column in fieldnames
        },
        "numeric_summary": numeric_summary,
        "quality_checks": {
            "exact_duplicate_rows": exact_duplicates,
            "exact_duplicate_row_rate": percentage(exact_duplicates, rows),
            "repeated_canonical_url_rows": repeated_canonical_rows,
            "repeated_canonical_url_row_rate": percentage(repeated_canonical_rows, rows),
            "invalid_rating_rows": sum(value < 1 or value > 5 for value in numeric_values["rate_clean"]),
            "invalid_cost_rows": sum(value <= 0 for value in numeric_values["cost_clean"]),
            "negative_vote_rows": sum(value < 0 for value in numeric_values["votes"]),
            "malformed_numeric_values": dict(malformed_numeric),
            "unexpected_online_order_values": unexpected_services["online_order"],
            "unexpected_book_table_values": unexpected_services["book_table"],
            "online_order_values": dict(service_values["online_order"]),
            "book_table_values": dict(service_values["book_table"]),
        },
    }
    (output_dir / "data_quality_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, output_dir / "data_quality_report.md")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit the Zomato CSV snapshot.")
    parser.add_argument("--input", type=Path, default=Path("zomato_cleaned.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args()
    report = audit(args.input, args.output_dir)
    print(f"Audited {report['profile']['row_count']:,} rows into {args.output_dir}")


if __name__ == "__main__":
    main()
