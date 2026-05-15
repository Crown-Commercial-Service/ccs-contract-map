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
from typing import Optional

import pandas as pd
from sklearn.model_selection import train_test_split


def split_and_save_datasets(
    data: pd.DataFrame, input_path: Path, train_ratio: float = 0.8
) -> tuple[Path, Path]:
    """
    Split data into train and test sets with stratified sampling and save as TSV.

    Args:
        data: DataFrame to split
        input_path: Original input file path (used for generating output names)
        train_ratio: Proportion of data for training set (default: 0.8)

    Returns:
        Tuple of (train_path, test_path) for the saved TSV files

    Raises:
        ValueError: If train_ratio is not in range (0.0, 1.0) or if any category
                   has fewer than 2 samples (required for stratification)
    """
    # Validate train_ratio
    if not 0.0 < train_ratio < 1.0:
        raise ValueError(
            f"train_ratio must be between 0.0 and 1.0 (exclusive), got {train_ratio}"
        )

    # Check that each category has at least 2 samples for stratification
    category_counts = data["Category"].value_counts()
    insufficient_categories = category_counts[category_counts < 2]
    if not insufficient_categories.empty:
        categories_str = ", ".join(
            f"'{cat}' ({count} sample{'s' if count != 1 else ''})"
            for cat, count in insufficient_categories.items()
        )
        raise ValueError(
            f"Cannot perform stratified split: the following categories have fewer "
            f"than 2 samples: {categories_str}. Each category needs at least 2 samples "
            f"for train/test splitting. Consider removing --train-ratio to skip splitting."
        )

    # Perform stratified train/test split
    train_data, test_data = train_test_split(
        data, train_size=train_ratio, stratify=data["Category"], random_state=42
    )

    # Generate output file paths (TSV format)
    input_stem = input_path.stem
    output_dir = input_path.parent
    train_path = output_dir / f"{input_stem}_train.tsv"
    test_path = output_dir / f"{input_stem}_test.tsv"

    # Save train and test sets as TSV (tab-separated to handle commas in text)
    train_data.to_csv(train_path, index=False, sep="\t")
    test_data.to_csv(test_path, index=False, sep="\t")

    # Print split statistics
    print(f"\n{'='*60}")
    print("Train/Test Split Statistics")
    print(f"{'='*60}")
    print(f"Train set: {len(train_data)} samples ({train_ratio*100:.1f}%)")
    print(f"Test set:  {len(test_data)} samples ({(1-train_ratio)*100:.1f}%)")
    print("\nCategory distribution:")
    print(f"{'Category':<40} {'Train':<8} {'Test':<8}")
    print("-" * 60)
    for category in sorted(data["Category"].unique()):
        train_count = (train_data["Category"] == category).sum()
        test_count = (test_data["Category"] == category).sum()
        print(f"{category:<40} {train_count:<8} {test_count:<8}")

    print(f"\nTrain set saved to: {train_path}")
    print(f"Test set saved to:  {test_path}")

    return train_path, test_path


def clean_and_normalize_data(
    input_path: Path, train_ratio: Optional[float] = None
) -> None:
    """
    Load data from Excel, apply normalization rules, and overwrite the input file.
    Optionally split into train/test sets with stratified sampling.

    Args:
        input_path: Path to input Excel file (will be overwritten)
        train_ratio: Optional proportion for train set (0.0-1.0). If provided,
                    creates {input_stem}_train.tsv and {input_stem}_test.tsv
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

    # Perform train/test split if requested
    if train_ratio is not None:
        try:
            split_and_save_datasets(data, input_path, train_ratio)
        except ValueError as e:
            print(f"\nWarning: Could not create train/test split: {e}")
            print("Only the cleaned full dataset was saved.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean and normalize truthset data for contract mapping evaluation."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to input Excel file with ground truth data (will be overwritten)",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=None,
        help=(
            "Proportion of data for training set (0.0-1.0). "
            "If provided, creates stratified train/test TSV files. "
            "Default: None (no splitting, only cleaned data saved)."
        ),
    )

    args = parser.parse_args()

    # Validate train_ratio if provided
    if args.train_ratio is not None and not 0.0 < args.train_ratio < 1.0:
        parser.error("--train-ratio must be between 0.0 and 1.0 (exclusive)")

    clean_and_normalize_data(args.input, train_ratio=args.train_ratio)


if __name__ == "__main__":
    main()
