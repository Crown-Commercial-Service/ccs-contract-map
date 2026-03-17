import argparse
import asyncio
import sys
from pathlib import Path

import pandas as pd
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
PROMPTS_DIR = REPO_ROOT / "prompts"
DEFAULT_TRUTH_SET = (
    REPO_ROOT / "data/input/AI Category Mapping - Category Desc Examples_new.csv"
)

# Ensure imports work when running this file directly from repo root.
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))



def _available_prompt_files() -> list[Path]:
    files = sorted(PROMPTS_DIR.glob("*.md"))
    return [path for path in files if path.is_file()]


def _resolve_prompt_file(prompt_name: str | None, mapper: str) -> Path:
    defaults = {
        "v1": "new_system_prompt.md",
        "v2": "system_prompt_v2.md",
    }

    selected_name = prompt_name or defaults[mapper]
    prompt_file = PROMPTS_DIR / selected_name

    if not prompt_file.exists():
        available = ", ".join(path.name for path in _available_prompt_files())
        raise FileNotFoundError(
            f"Prompt '{selected_name}' not found in '{PROMPTS_DIR}'. "
            f"Available prompts: {available}"
        )

    return prompt_file


def _load_truth_set(truth_set_path: Path) -> pd.DataFrame:
    if not truth_set_path.exists():
        raise FileNotFoundError(f"Truth set file not found: {truth_set_path}")

    df = pd.read_csv(truth_set_path)
    required_cols = {"Description", "Category"}
    missing = required_cols.difference(df.columns)
    if missing:
        raise ValueError(
            f"Truth set must include columns {sorted(required_cols)}. Missing: {sorted(missing)}"
        )

    return df.dropna(subset=["Description", "Category"]).reset_index(drop=True)


async def _classify_description(description: str, mapper: str, prompt_file: Path) -> str:
    if mapper == "v1":
        from core.classification_v1 import contract_mapper

        return contract_mapper(
            system_prompt_file_location=prompt_file,
            user_contract_description=description,
        )

    from core.classification_v2 import contract_mapper_v2
    return await contract_mapper_v2(
        user_contract_description=description,
        system_prompt_file_location=prompt_file,
    )


async def run_evaluation(
    truth_set_path: Path,
    mapper: str,
    prompt_name: str | None,
    output_path: Path | None,
) -> None:
    prompt_file = _resolve_prompt_file(prompt_name=prompt_name, mapper=mapper)
    df = _load_truth_set(truth_set_path=truth_set_path)

    descriptions = df["Description"].astype(str).tolist()
    categories = df["Category"].astype(str).tolist()

    predictions: list[str] = []
    correct = 0

    for description, expected in zip(descriptions, categories):
        prediction = await _classify_description(
            description=description,
            mapper=mapper,
            prompt_file=prompt_file,
        )
        predictions.append(prediction)
        is_correct = prediction == expected
        correct += int(is_correct)
        print(f"expected: {expected} | predicted: {prediction} | correct: {is_correct}")

    accuracy = (correct / len(predictions)) * 100 if predictions else 0.0
    print(f"\n{mapper.upper()} accuracy: {accuracy:.2f}% on {len(predictions)} samples")

    if output_path is None:
        output_path = REPO_ROOT / f"data/results/eval_{mapper}_{prompt_file.stem}.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_df = df[["Category", "Description"]].copy()
    result_df["AI classification"] = predictions
    result_df["correct"] = result_df["Category"] == result_df["AI classification"]
    result_df.to_csv(output_path, index=False)
    print(f"Saved results to: {output_path}")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run contract mapping evaluation with selectable mapper and prompt."
    )
    parser.add_argument(
        "--truth-set",
        type=Path,
        default=DEFAULT_TRUTH_SET,
        help="Path to truth set CSV file (must have Description and Category columns).",
    )
    parser.add_argument(
        "--mapper",
        choices=["v1", "v2"],
        required=True,
        help="Mapper version to run.",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Prompt file name from prompts/ (example: system_prompt_v2.md).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output CSV path. Defaults to data/results/eval_<mapper>_<prompt>.csv.",
    )
    parser.add_argument(
        "--list-prompts",
        action="store_true",
        help="List available prompt files in prompts/ and exit.",
    )
    return parser


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()

    if args.list_prompts:
        print("Available prompts:")
        for prompt in _available_prompt_files():
            print(f"- {prompt.name}")
        return

    asyncio.run(
        run_evaluation(
            truth_set_path=args.truth_set,
            mapper=args.mapper,
            prompt_name=args.prompt,
            output_path=args.output,
        )
    )


if __name__ == "__main__":
    main()
