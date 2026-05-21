import argparse
import json
from pathlib import Path

import pandas as pd
import ast

from src.utils.llm_keywords_finder import keywords_finder_llm


def extract_description(val):
    """Extract description from structured data."""
    try:
        d = ast.literal_eval(val)
        return d.get("description", "")
    except (ValueError, SyntaxError, AttributeError):
        return ""


def build_semantic_anchors(
    corpus_path: Path, output_path: Path, max_categories: int = 3
) -> dict:
    """
    Build semantic anchors registry from training corpus.

    Args:
        corpus_path: Path to training TSV file
        output_path: Path to save semantic anchors JSON
        max_categories: Maximum number of categories a word can appear in (default: 3)

    Returns:
        Dictionary of semantic anchors by category
    """
    # --- DATA PREPARATION ---
    data = pd.read_csv(str(corpus_path), sep="\t")
    data_to_analyse = data[data["Category"].notna()].copy()

    data_to_analyse["clean_description"] = data_to_analyse["Description"].apply(
        extract_description
    )

    # --- KEYWORD EXTRACTION LOOP ---
    grouped_data = data_to_analyse.groupby("Category")
    registry = {}

    for category, group in grouped_data:
        print(f"Processing category: {category}")
        primary_store = set()
        secondary_store = set()

        for text in group["clean_description"].tolist():
            # Using the LLM to find keywords for each individual contract
            primary, secondary = keywords_finder_llm(text)
            primary_store.update(primary)
            secondary_store.update(secondary)

        registry[category] = {
            "primary": list(primary_store),
            "secondary": list(secondary_store),
        }

    # --- 1. GLOBAL DE-DUPLICATION ---
    word_ownership = {}
    for cat, content in registry.items():
        for word in content["primary"]:
            word_clean = word.lower().strip()
            if word_clean not in word_ownership:
                word_ownership[word_clean] = []
            word_ownership[word_clean].append(cat)

    for cat in list(registry.keys()):
        orig_primary = registry[cat]["primary"]
        orig_secondary = registry[cat]["secondary"]
        final_primary = []
        final_secondary = list(orig_secondary)

        for word in orig_primary:
            word_clean = word.lower().strip()
            if len(word_ownership[word_clean]) > 1:
                if word not in final_secondary:
                    final_secondary.append(word)
            else:
                final_primary.append(word)

        registry[cat] = [final_primary, final_secondary]

    # --- 2. OUTSIDE TAXONOMY PURGE ---
    # Ensures "Outside New Taxonomy" doesn't claim words belonging to real categories
    if "Outside New Taxonomy" in registry:
        real_category_words = set()
        for cat, content in registry.items():
            if cat != "Outside New Taxonomy":
                real_category_words.update(
                    [w.lower().strip() for w in content[0]]
                )  # Primary
                real_category_words.update(
                    [w.lower().strip() for w in content[1]]
                )  # Secondary

        o_primary, o_secondary = registry["Outside New Taxonomy"]

        # Remove words from 'Outside' if they exist anywhere else in the real taxonomy
        registry["Outside New Taxonomy"] = [
            [w for w in o_primary if w.lower().strip() not in real_category_words],
            [w for w in o_secondary if w.lower().strip() not in real_category_words],
        ]
        print("Purged overlapping keywords from 'Outside New Taxonomy'.")

    # --- 3. GLOBAL FREQUENCY FILTER (NOISE CANCELLATION) ---
    # If a word appears in more than max_categories, it's generic noise and should be deleted
    global_word_frequency = {}
    for cat, content in registry.items():
        all_words = set(content[0] + content[1])
        for word in all_words:
            w_clean = word.lower().strip()
            global_word_frequency[w_clean] = global_word_frequency.get(w_clean, 0) + 1

    final_cleaned_registry = {}

    for cat, (primary, secondary) in registry.items():
        clean_p = [
            w
            for w in primary
            if global_word_frequency[w.lower().strip()] <= max_categories
        ]
        clean_s = [
            w
            for w in secondary
            if global_word_frequency[w.lower().strip()] <= max_categories
        ]
        final_cleaned_registry[cat] = [clean_p, clean_s]

    # --- FINAL SAVE ---
    # sort alphabetically for readability
    sorted_registry = {
        cat: [sorted(primary), sorted(secondary)]
        for cat, (primary, secondary) in sorted(final_cleaned_registry.items())
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sorted_registry, f, indent=4, ensure_ascii=False)

    print(
        f"Successfully saved {len(sorted_registry)} cleaned categories to {output_path}"
    )

    return sorted_registry


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract semantic anchors from training corpus using LLM-based keyword extraction."
    )
    parser.add_argument(
        "--input-train-tsv",
        type=Path,
        required=True,
        help="Path to training TSV file with Description and Category columns",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        required=True,
        help="Path to save semantic anchors JSON output",
    )
    parser.add_argument(
        "--max-categories",
        type=int,
        default=3,
        help="Maximum number of categories a word can appear in before being filtered (default: 3)",
    )

    args = parser.parse_args()

    # Validate input file exists
    if not args.input_train_tsv.exists():
        raise FileNotFoundError(f"Training file not found: {args.input_train_tsv}")

    # Build semantic anchors
    build_semantic_anchors(
        corpus_path=args.input_train_tsv,
        output_path=args.output_json,
        max_categories=args.max_categories,
    )


if __name__ == "__main__":
    main()
