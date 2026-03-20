import argparse
import asyncio
import os
import sys
import time
from contextlib import nullcontext
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

import pandas as pd

load_dotenv()

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


async def _classify_description(
    description: str, mapper: str, prompt_file: Path
) -> str:
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


def _get_mlflow_module() -> Any | None:
    """Import Azure MLflow module (azureml-mlflow extends standard mlflow)."""
    try:
        import importlib

        return importlib.import_module("mlflow")
    except ModuleNotFoundError:
        return None


async def run_evaluation(
    truth_set_path: Path,
    mapper: str,
    prompt_name: str | None,
    output_path: Path | None,
    mlflow_enabled: bool = False,
    mlflow_tracking_uri: str | None = None,
    mlflow_experiment_name: str | None = None,
    mlflow_run_name: str | None = None,
) -> None:
    mlflow_module = None
    if mlflow_enabled:
        mlflow_module = _get_mlflow_module()
        if mlflow_module is None:
            raise ModuleNotFoundError(
                "Azure MLflow is not installed. Install with 'pip install azureml-mlflow' "
                "and authenticate using 'az login'."
            )

    prompt_file = _resolve_prompt_file(prompt_name=prompt_name, mapper=mapper)
    df = _load_truth_set(truth_set_path=truth_set_path)

    descriptions = df["Description"].astype(str).tolist()
    categories = df["Category"].astype(str).tolist()

    predictions: list[str] = []
    correct = 0

    if output_path is None:
        output_path = REPO_ROOT / f"data/results/eval_{mapper}_{prompt_file.stem}.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if mlflow_enabled and mlflow_module is not None:
        tracking_uri = mlflow_tracking_uri or os.getenv("MLFLOW_TRACKING_URI")
        if not tracking_uri:
            raise ValueError(
                "MLflow tracking URI is required when --mlflow is set. "
                "Set --mlflow-tracking-uri or MLFLOW_TRACKING_URI."
            )
        experiment_name = mlflow_experiment_name or os.getenv(
            "MLFLOW_EXPERIMENT_NAME", "ContractMap-Evaluation"
        )
        mlflow_module.set_tracking_uri(tracking_uri)
        mlflow_module.set_experiment(experiment_name)
        run_context = mlflow_module.start_run(run_name=mlflow_run_name)
    else:
        run_context = nullcontext()

    with run_context:
        if mlflow_enabled and mlflow_module is not None:
            mlflow_module.log_param("mapper", mapper)
            mlflow_module.log_param("truth_set_path", str(truth_set_path.resolve()))
            mlflow_module.log_param("prompt_name", prompt_name or prompt_file.name)
            mlflow_module.log_param("prompt_path", str(prompt_file.resolve()))
            mlflow_module.log_param("num_samples", len(descriptions))
            mlflow_module.log_artifact(
                str(prompt_file.resolve()), artifact_path="prompts"
            )

        start_time = time.perf_counter()
        for description, expected in zip(descriptions, categories):
            prediction = await _classify_description(
                description=description,
                mapper=mapper,
                prompt_file=prompt_file,
            )
            predictions.append(prediction)
            is_correct = prediction == expected
            correct += int(is_correct)
            print(
                f"expected: {expected} | predicted: {prediction} | correct: {is_correct}"
            )

        elapsed_seconds = time.perf_counter() - start_time
        accuracy = (correct / len(predictions)) * 100 if predictions else 0.0
        print(
            f"\n{mapper.upper()} accuracy: {accuracy:.2f}% on {len(predictions)} samples"
        )

        result_df = df[["Category", "Description"]].copy()
        result_df["AI classification"] = predictions
        result_df["correct"] = result_df["Category"] == result_df["AI classification"]
        result_df.to_csv(output_path, index=False)
        print(f"Saved results to: {output_path}")

        if mlflow_enabled and mlflow_module is not None:
            mlflow_module.log_metric("accuracy_percent", accuracy)
            mlflow_module.log_metric("accuracy_fraction", accuracy / 100)
            mlflow_module.log_metric("correct_predictions", float(correct))
            mlflow_module.log_metric("evaluation_duration_seconds", elapsed_seconds)
            mlflow_module.log_artifact(
                str(output_path.resolve()), artifact_path="results"
            )


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
    parser.add_argument(
        "--mlflow",
        action="store_true",
        help="Enable Azure MLflow experiment tracking.",
    )
    parser.add_argument(
        "--mlflow-tracking-uri",
        type=str,
        default=None,
        help="Azure MLflow tracking URI (azureml:// scheme). Defaults to MLFLOW_TRACKING_URI env var.",
    )
    parser.add_argument(
        "--mlflow-experiment-name",
        type=str,
        default=None,
        help="Optional Azure MLflow experiment name. Defaults to MLFLOW_EXPERIMENT_NAME or ContractMap-Evaluation.",
    )
    parser.add_argument(
        "--mlflow-run-name",
        type=str,
        default=None,
        help="Optional Azure MLflow run name.",
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
            mlflow_enabled=args.mlflow,
            mlflow_tracking_uri=args.mlflow_tracking_uri,
            mlflow_experiment_name=args.mlflow_experiment_name,
            mlflow_run_name=args.mlflow_run_name,
        )
    )


if __name__ == "__main__":
    main()
