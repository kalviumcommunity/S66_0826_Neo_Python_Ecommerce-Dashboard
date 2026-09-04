"""Profile raw CSV datasets for common data-quality issues."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"
PROFILE_REPORTS_DIR = OUTPUT_DIR / "profile_reports"


def _finite_float(value: Any) -> float | None:
    """Return a JSON-safe float, or None for non-finite values."""
    value = float(value)
    return value if np.isfinite(value) else None


def profile_nulls_and_duplicates(df: pd.DataFrame) -> dict[str, Any]:
    """Compute null percentages and duplicate counts per column and row."""
    row_count = len(df)
    profile: dict[str, Any] = {
        "null_counts": {},
        "null_percentages": {},
        "exact_duplicate_count": int(df.duplicated().sum()),
    }

    for col in df.columns:
        null_count = int(df[col].isna().sum())
        null_pct = (null_count / row_count) * 100 if row_count else 0.0
        profile["null_counts"][col] = null_count
        profile["null_percentages"][col] = round(null_pct, 2)

    duplicate_pct = (
        profile["exact_duplicate_count"] / row_count * 100 if row_count else 0.0
    )
    profile["duplicate_percentage"] = round(duplicate_pct, 2)
    return profile


def profile_numerical_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Summarise numerical columns with min, max, mean, median, and std."""
    numerical_cols = df.select_dtypes(include=[np.number]).columns
    stats: dict[str, dict[str, Any]] = {}

    for col in numerical_cols:
        stats[col] = {
            "min": _finite_float(round(df[col].min(), 2)),
            "max": _finite_float(round(df[col].max(), 2)),
            "mean": _finite_float(round(df[col].mean(), 2)),
            "median": _finite_float(round(df[col].median(), 2)),
            "std": _finite_float(round(df[col].std(), 2)),
            "null_count": int(df[col].isnull().sum()),
        }

    numerical_stats = pd.DataFrame(stats).T
    if numerical_stats.empty:
        return numerical_stats

    # DataFrame construction can promote None to NaN in numeric columns.
    # Convert the aggregate columns back to object dtype so None is preserved.
    for metric in ("min", "max", "mean", "median", "std"):
        numerical_stats[metric] = (
            numerical_stats[metric]
            .astype(object)
            .where(numerical_stats[metric].notna(), None)
        )

    numerical_stats["null_count"] = numerical_stats["null_count"].astype(int)
    return numerical_stats


def _is_identifier_like(column_name: str) -> bool:
    """Return whether a column name indicates an identifier value."""
    normalized_name = column_name.lower()
    return bool(
        re.search(r"(?:^|_)id$", normalized_name)
        or "unique_id" in normalized_name
    )


def profile_categorical_columns(
    df: pd.DataFrame, top_n: int = 5
) -> dict[str, dict[str, Any]]:
    """Summarise object columns without exposing identifier values."""
    categorical_cols = df.select_dtypes(include=["object"]).columns
    profile: dict[str, dict[str, Any]] = {}

    for col in categorical_cols:
        top_values = (
            {}
            if _is_identifier_like(str(col))
            else df[col].value_counts().head(top_n).to_dict()
        )
        profile[col] = {
            "unique_count": int(df[col].nunique()),
            "top_values": top_values,
            "null_count": int(df[col].isnull().sum()),
        }

    return profile


def identify_quality_issues(
    df: pd.DataFrame, null_threshold: float = 30, duplicate_threshold: float = 5
) -> list[dict[str, str]]:
    """Identify quality problems based on null, duplicate, and range thresholds."""
    issues: list[dict[str, str]] = []
    row_count = len(df)

    null_pcts = (
        df.isnull().sum() / row_count * 100 if row_count else df.isnull().sum() * 0
    )
    for col, pct in null_pcts.items():
        if pct > null_threshold:
            issues.append(
                {
                    "type": "High nulls",
                    "column": col,
                    "severity": "HIGH",
                    "value": f"{pct:.1f}% missing",
                    "recommendation": "Consider imputation or column exclusion",
                }
            )

    dup_count = int(df.duplicated().sum())
    dup_pct = dup_count / row_count * 100 if row_count else 0.0
    if dup_pct > duplicate_threshold:
        issues.append(
            {
                "type": "High duplicates",
                "column": "Full row",
                "severity": "HIGH",
                "value": f"{dup_pct:.1f}% duplicated",
                "recommendation": "Deduplication required before analysis",
            }
        )

    for col in df.select_dtypes(include=[np.number]).columns:
        if "amount" in col.lower() and (df[col] < 0).any():
            issues.append(
                {
                    "type": "Invalid range",
                    "column": col,
                    "severity": "MEDIUM",
                    "value": "Contains negative values",
                    "recommendation": "Investigate negative entries",
                }
            )

    return issues


def generate_profile_report(
    df: pd.DataFrame, filepath: str | Path, output_path: str | Path | None = None
) -> dict[str, Any]:
    """Generate a complete data-quality report and optionally save it to JSON."""
    filepath = str(filepath)
    report: dict[str, Any] = {
        "dataset": filepath,
        "record_count": len(df),
        "column_count": len(df.columns),
        "nulls_and_duplicates": profile_nulls_and_duplicates(df),
        "numerical_stats": profile_numerical_columns(df).to_dict(),
        "categorical_stats": profile_categorical_columns(df),
        "quality_issues": identify_quality_issues(df),
    }

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as report_file:
            json.dump(
                report,
                report_file,
                indent=2,
                default=str,
                allow_nan=False,
            )

    print(f"\n{'=' * 60}")
    print(f"DATA QUALITY PROFILE: {filepath}")
    print(f"{'=' * 60}")
    print(f"Records: {report['record_count']}")
    print(f"Columns: {report['column_count']}")
    print(f"\nQuality Issues Found: {len(report['quality_issues'])}")
    for issue in report["quality_issues"]:
        print(f"  [{issue['severity']}] {issue['type']} in {issue['column']}")
        print(f"    Value: {issue['value']} -> {issue['recommendation']}")
    print(f"{'=' * 60}\n")
    return report


def profile_all_datasets(
    raw_dir: str | Path = RAW_DATA_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    top_n: int = 5,
) -> dict[str, Any]:
    """Profile every CSV in ``raw_dir`` and save individual and summary reports."""
    raw_dir = Path(raw_dir)
    output_dir = Path(output_dir)
    reports_dir = output_dir / "profile_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    dataset_summaries: list[dict[str, Any]] = []
    csv_files = sorted(raw_dir.glob("*.csv"))
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        report = generate_profile_report(
            df,
            csv_file.name,
            reports_dir / f"{csv_file.stem}_profile.json",
        )
        # Recompute categorical data using the requested batch top_n value.
        report["categorical_stats"] = profile_categorical_columns(df, top_n=top_n)
        with (reports_dir / f"{csv_file.stem}_profile.json").open(
            "w", encoding="utf-8"
        ) as report_file:
            json.dump(
                report,
                report_file,
                indent=2,
                default=str,
                allow_nan=False,
            )

        dataset_summaries.append(
            {
                "dataset": csv_file.name,
                "record_count": len(df),
                "column_count": len(df.columns),
                "quality_issue_count": len(report["quality_issues"]),
                "duplicate_percentage": report["nulls_and_duplicates"][
                    "duplicate_percentage"
                ],
            }
        )

    summary = {"dataset_count": len(dataset_summaries), "datasets": dataset_summaries}
    with (output_dir / "profile_summary.json").open(
        "w", encoding="utf-8"
    ) as summary_file:
        json.dump(summary, summary_file, indent=2, default=str)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile all raw CSV datasets.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--top-n", type=int, default=5)
    args = parser.parse_args()
    summary = profile_all_datasets(args.raw_dir, args.output_dir, args.top_n)
    print(f"Profiled {summary['dataset_count']} dataset(s).")


if __name__ == "__main__":
    main()
