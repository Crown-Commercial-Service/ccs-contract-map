#!/usr/bin/env python3
"""
Clean and normalize truthset data for contract mapping evaluation.

This script applies consistent normalization rules to ground truth data:
- Converts '&' to 'and'
- Removes extra whitespace
- Standardizes category names (singular/plural, inconsistent naming)
"""

import argparse
from pathlib import Path

import pandas as pd


def clean_and_normalize_data(input_path: Path) -> None:
    """
    Load data from Excel, apply normalization rules, and overwrite the input file.

    Args:
        input_path: Path to input Excel file (will be overwritten)
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"Loading data from: {input_path}")
    data = pd.read_excel(input_path)

    # Validate required columns
    required_cols = {"Title", "Description", "Category"}
    missing = required_cols.difference(data.columns)
    if missing:
        raise ValueError(
            f"Input file must include columns {sorted(required_cols)}. "
            f"Missing: {sorted(missing)}"
        )

    print(f"Loaded {len(data)} rows")

    # 1. Clean the 'Category' column
    # Convert '&' to 'and' and remove extra trailing spaces
    print("Normalizing 'Category' column...")
    data["Category"] = (
        data["Category"]
        .astype(str)
        .str.replace(r"\s*&\s*", " and ", regex=True)
        .str.replace(r"\s+", " ", regex=True)  # Remove double spaces
        .str.strip()
    )

    # 2. Standardize specific category names
    normalization_map = {
        "Network Service": "Network Services",
        "Cloud & Hosting": "Cloud and Hosting",
        "HR & Workforce Services": "HR and Workforce Services",
        "Digital & Technology Services": "Digital and Technology Services",
    }

    print(f"Applying {len(normalization_map)} normalization rules...")
    data["Category"] = data["Category"].replace(normalization_map)

    # Also normalize AI_CategoryMatch if it exists
    if "AI_CategoryMatch" in data.columns:
        print("Normalizing 'AI_CategoryMatch' column...")
        data["AI_CategoryMatch"] = data["AI_CategoryMatch"].replace(normalization_map)

    # Remove rows with missing required data
    initial_count = len(data)
    data = data.dropna(subset=["Category", "Description"]).reset_index(drop=True)
    dropped_count = initial_count - len(data)

    if dropped_count > 0:
        print(f"Dropped {dropped_count} rows with missing data")

    # Save cleaned data (overwrite input file)
    data.to_excel(input_path, index=False)
    print(f"\nCleaned data saved to: {input_path}")
    print(f"Final row count: {len(data)}")

    # Show unique categories
    unique_categories = sorted(data["Category"].unique())
    print(f"\nUnique categories ({len(unique_categories)}):")
    for cat in unique_categories:
        count = (data["Category"] == cat).sum()
        print(f"  - {cat}: {count} rows")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean and normalize truthset data for contract mapping evaluation."
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Path to input Excel file with ground truth data (will be overwritten)",
    )

    args = parser.parse_args()

    clean_and_normalize_data(args.input)


if __name__ == "__main__":
    main()
