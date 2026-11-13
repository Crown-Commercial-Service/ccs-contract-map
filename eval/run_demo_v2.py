import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from contractmap import get_classifier

import pandas as pd
import asyncio

"""
this script demos LLMs shows ability to classify CCS category
by looking at contract description
"""


async def main():
    df = pd.read_csv(
        REPO_ROOT / "data/input/AI Category Mapping - Category Desc Examples_new.csv"
    )
    df = df.dropna(subset=["Description"]).copy()
    df = df.reset_index(drop=True)

    list_descriptions = df["Description"].values.tolist()
    list_category = df["Category"].values.tolist()

    classifier = get_classifier()

    count_correct = 0
    list_results = []

    for description, category in zip(list_descriptions, list_category):
        result = await classifier.classify(description)
        list_results.append(result.category)
        print(f" actual:{category}  AI:{result.category}, {category in result.category}")
        if category == result.category:
            count_correct += 1
        print()

    print(
        f" AI accuracy:{(count_correct/len(list_descriptions))*100}% on {len(list_results)} samples"
    )

    new_df = df[["Category", "Description"]].copy()
    new_df["AI classification"] = list_results

    output_path = REPO_ROOT / "data/results/AI_v2_results_optimised.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    new_df.to_csv(output_path)
    print("experiment completed")


if __name__ == "__main__":
    asyncio.run(main())