#!/usr/bin/env python3
"""
Grid search wrapper for contract mapping evaluation.

This script reads threshold and margin parameters from params.yaml and runs
the evaluation script for all parameter combinations, logging results to MLflow.
"""

import argparse
import subprocess
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_params(params_file: Path) -> dict:
    """Load parameters from params.yaml file."""
    if not params_file.exists():
        raise FileNotFoundError(f"Parameters file not found: {params_file}")

    with open(params_file, "r") as f:
        params = yaml.safe_load(f)

    return params


def run_evaluation(
    eval_script: Path,
    truthset: Path,
    threshold: int,
    margin: int,
    mlflow_experiment_name: str,
) -> None:
    """
    Run a single evaluation with the given parameters.

    Args:
        eval_script: Path to run_eval.py
        truthset: Path to truthset file
        threshold: Threshold parameter value
        margin: Margin parameter value
        mlflow_experiment_name: Name of MLflow experiment
    """
    run_name = f"t{threshold}_m{margin}"

    print(f"\n{'='*60}")
    print(f"Running evaluation: {run_name}")
    print(f"  Threshold: {threshold}")
    print(f"  Margin: {margin}")
    print(f"{'='*60}\n")

    # Build command
    cmd = [
        sys.executable,  # Use the same Python interpreter
        str(eval_script),
        "--truthset",
        str(truthset),
        "--threshold",
        str(threshold),
        "--margin",
        str(margin),
        "--mlflow-run-name",
        run_name,
        "--mlflow-experiment-name",
        mlflow_experiment_name,
    ]

    # Run evaluation
    result = subprocess.run(cmd, check=False)

    if result.returncode != 0:
        print(
            f"WARNING: Evaluation {run_name} failed with exit code {result.returncode}"
        )
    else:
        print(f"✓ Completed: {run_name}")


def main():
    """Main entry point for grid search."""
    parser = argparse.ArgumentParser(
        description="Run grid search over threshold and margin parameters."
    )
    parser.add_argument(
        "--params-file",
        type=Path,
        default=REPO_ROOT / "params.yaml",
        help="Path to params.yaml file (default: repo_root/params.yaml)",
    )
    parser.add_argument(
        "--eval-script",
        type=Path,
        default=REPO_ROOT / "eval" / "run_eval.py",
        help="Path to evaluation script (default: eval/run_eval.py)",
    )
    parser.add_argument(
        "--truthset",
        type=Path,
        default=None,
        help="Path to truthset file (overrides params.yaml)",
    )

    args = parser.parse_args()

    # Load parameters
    print(f"Loading parameters from: {args.params_file}")
    params = load_params(args.params_file)

    # Extract configuration
    thresholds = params["gridsearch"]["thresholds"]
    margins = params["gridsearch"]["margins"]
    mlflow_experiment_name = params["mlflow"]["experiment_name"]

    # Determine truthset path
    if args.truthset:
        truthset_path = args.truthset
    else:
        truthset_path = REPO_ROOT / params["data"]["input_excel"]

    # Validate paths
    if not args.eval_script.exists():
        raise FileNotFoundError(f"Evaluation script not found: {args.eval_script}")

    if not truthset_path.exists():
        raise FileNotFoundError(f"Truthset file not found: {truthset_path}")

    # Calculate total runs
    total_runs = len(thresholds) * len(margins)

    print(f"\n{'='*60}")
    print("Grid Search Configuration")
    print(f"{'='*60}")
    print(f"Thresholds: {thresholds}")
    print(f"Margins: {margins}")
    print(f"Total combinations: {total_runs}")
    print(f"MLflow experiment: {mlflow_experiment_name}")
    print(f"Truthset: {truthset_path}")
    print(f"{'='*60}\n")

    # Run grid search
    current_run = 0
    failed_runs = []

    for threshold in thresholds:
        for margin in margins:
            current_run += 1
            print(f"\nProgress: {current_run}/{total_runs}")

            try:
                run_evaluation(
                    eval_script=args.eval_script,
                    truthset=truthset_path,
                    threshold=threshold,
                    margin=margin,
                    mlflow_experiment_name=mlflow_experiment_name,
                )
            except Exception as e:
                run_name = f"t{threshold}_m{margin}"
                print(f"ERROR: Failed to run {run_name}: {e}")
                failed_runs.append(run_name)

    # Write completion marker
    completion_marker = REPO_ROOT / params["outputs"]["completion_marker"]
    completion_marker.parent.mkdir(parents=True, exist_ok=True)

    with open(completion_marker, "w") as f:
        f.write("Grid search completed successfully.\n")
        f.write(f"Total runs: {total_runs}\n")
        f.write(f"Successful runs: {total_runs - len(failed_runs)}\n")
        f.write(f"Failed runs: {len(failed_runs)}\n")
        if failed_runs:
            f.write("\nFailed run names:\n")
            for run_name in failed_runs:
                f.write(f"  - {run_name}\n")

    print(f"\n{'='*60}")
    print("Grid Search Complete!")
    print(f"{'='*60}")
    print(f"Total runs: {total_runs}")
    print(f"Successful runs: {total_runs - len(failed_runs)}")
    print(f"Failed runs: {len(failed_runs)}")
    if failed_runs:
        print("\nFailed runs:")
        for run_name in failed_runs:
            print(f"  - {run_name}")
    print(f"\nCompletion marker written to: {completion_marker}")
    print(f"{'='*60}\n")

    # Exit with error if any runs failed
    if failed_runs:
        sys.exit(1)


if __name__ == "__main__":
    main()
