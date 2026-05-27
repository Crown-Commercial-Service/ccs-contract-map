"""
Plot distribution of Heuristic scores from an MLflow run.

This script:
1. Accepts an MLflow run name as an argument
2. Connects to the MLflow server and retrieves the run
3. Downloads the CSV results artifact from that run
4. Plots a distribution of the Heuristic_Score values
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up paths
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _get_mlflow_module() -> Any | None:
    """Import Azure MLflow module (azureml-mlflow extends standard mlflow)."""
    try:
        import importlib

        return importlib.import_module("mlflow")
    except ModuleNotFoundError:
        return None


def _get_matplotlib() -> Any | None:
    """Import matplotlib.pyplot."""
    try:
        import importlib

        return importlib.import_module("matplotlib.pyplot")
    except ModuleNotFoundError:
        return None


def find_run_by_name(mlflow_module: Any, experiment_name: str, run_name: str) -> Any:
    """
    Find an MLflow run by its name within a specific experiment.

    Args:
        mlflow_module: The mlflow module
        experiment_name: Name of the MLflow experiment
        run_name: Name of the run to find

    Returns:
        MLflow Run object

    Raises:
        ValueError: If run not found or multiple runs found
    """
    # Get the experiment
    experiment = mlflow_module.get_experiment_by_name(experiment_name)
    if experiment is None:
        raise ValueError(f"Experiment '{experiment_name}' not found")

    # Search for runs with the specified name
    runs = mlflow_module.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string=f"tags.mlflow.runName = '{run_name}'",
        output_format="list",
    )

    if not runs:
        raise ValueError(
            f"No run found with name '{run_name}' in experiment '{experiment_name}'"
        )

    if len(runs) > 1:
        print(
            f"Warning: Found {len(runs)} runs with name '{run_name}'. Using the most recent."
        )
        # Sort by start time (most recent first)
        runs.sort(key=lambda r: r.info.start_time, reverse=True)

    return runs[0]


def download_results_csv(mlflow_module: Any, run: Any, temp_dir: Path) -> Path:
    """
    Download the results CSV artifact from an MLflow run.

    Args:
        mlflow_module: The mlflow module
        run: MLflow Run object
        temp_dir: Temporary directory to download artifacts to

    Returns:
        Path to the downloaded CSV file

    Raises:
        FileNotFoundError: If no CSV found in results artifacts
    """
    run_id = run.info.run_id

    # Download all artifacts from the results folder
    artifacts_path = mlflow_module.artifacts.download_artifacts(
        run_id=run_id, artifact_path="results", dst_path=str(temp_dir)
    )

    artifacts_dir = Path(artifacts_path)

    # Find CSV files in the downloaded artifacts
    csv_files = list(artifacts_dir.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV file found in results artifacts for run '{run.data.tags.get('mlflow.runName', run_id)}'"
        )

    if len(csv_files) > 1:
        print(f"Warning: Found {len(csv_files)} CSV files. Using: {csv_files[0].name}")

    return csv_files[0]


def plot_heuristic_distribution(
    csv_path: Path, run_name: str, output_path: Path | None = None, show: bool = True
) -> None:
    """
    Plot distribution of Heuristic_Score values from a results CSV.

    Args:
        csv_path: Path to the CSV file with results
        run_name: Name of the MLflow run (for plot title)
        output_path: Optional path to save the plot image
        show: Whether to display the plot interactively
    """
    plt = _get_matplotlib()
    if plt is None:
        raise ModuleNotFoundError(
            "matplotlib is required for plotting. "
            "Install with: pip install matplotlib"
        )

    # Load the CSV
    df = pd.read_csv(csv_path)

    # Check if Heuristic_Score column exists
    if "Heuristic_Score" not in df.columns:
        raise ValueError(
            f"CSV file does not contain 'Heuristic_Score' column. "
            f"Available columns: {', '.join(df.columns)}"
        )

    # Get heuristic scores and remove any NaN values
    heuristic_scores = df["Heuristic_Score"].dropna()

    if len(heuristic_scores) == 0:
        raise ValueError("No valid Heuristic_Score values found in the CSV")

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot histogram
    ax.hist(heuristic_scores, bins=30, edgecolor="black", alpha=0.7)

    # Add labels and title
    ax.set_xlabel("Heuristic Score", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.set_title(f"Distribution of Heuristic Scores\nRun: {run_name}", fontsize=14)

    # Add grid for better readability
    ax.grid(axis="y", alpha=0.3)

    # Add statistics as text
    stats_text = (
        f"Count: {len(heuristic_scores)}\n"
        f"Mean: {heuristic_scores.mean():.2f}\n"
        f"Median: {heuristic_scores.median():.2f}\n"
        f"Std Dev: {heuristic_scores.std():.2f}\n"
        f"Min: {heuristic_scores.min():.2f}\n"
        f"Max: {heuristic_scores.max():.2f}"
    )
    ax.text(
        0.98,
        0.97,
        stats_text,
        transform=ax.transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        fontsize=10,
    )

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Save if output path specified
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Plot saved to: {output_path}")

    # Show plot if requested
    if show:
        plt.show()

    plt.close()


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Plot distribution of Heuristic scores from an MLflow run"
    )
    parser.add_argument("run_name", type=str, help="Name of the MLflow run to analyze")
    parser.add_argument(
        "--experiment",
        type=str,
        default=None,
        help="MLflow experiment name (default: from MLFLOW_EXPERIMENT_NAME env var or 'ContractMap-KeywordLLM-Evaluation')",
    )
    parser.add_argument(
        "--tracking-uri",
        type=str,
        default=None,
        help="MLflow tracking URI (default: from MLFLOW_TRACKING_URI env var)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to save the plot image (e.g., plot.png)",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Don't display the plot interactively (useful when only saving to file)",
    )

    args = parser.parse_args()

    # Get MLflow module
    mlflow_module = _get_mlflow_module()
    if mlflow_module is None:
        print(
            "Error: Azure MLflow is not installed. "
            "Install with: pip install azureml-mlflow",
            file=sys.stderr,
        )
        sys.exit(1)

    # Get tracking URI
    tracking_uri = args.tracking_uri or os.getenv("MLFLOW_TRACKING_URI")
    if not tracking_uri:
        print(
            "Error: MLflow tracking URI is required. "
            "Set --tracking-uri or MLFLOW_TRACKING_URI env var.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Get experiment name
    experiment_name = args.experiment or os.getenv(
        "MLFLOW_EXPERIMENT_NAME", "ContractMap-KeywordLLM-Evaluation"
    )

    print(f"Connecting to MLflow at: {tracking_uri}")
    print(f"Experiment: {experiment_name}")
    print(f"Looking for run: {args.run_name}")

    # Set MLflow tracking URI
    mlflow_module.set_tracking_uri(tracking_uri)

    try:
        # Find the run
        print("Searching for run...")
        run = find_run_by_name(mlflow_module, experiment_name, args.run_name)
        print(f"Found run: {run.info.run_id}")

        # Download artifacts to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            print("Downloading results CSV...")
            csv_path = download_results_csv(mlflow_module, run, Path(temp_dir))
            print(f"Downloaded: {csv_path.name}")

            # Plot the distribution
            print("Generating plot...")
            plot_heuristic_distribution(
                csv_path=csv_path,
                run_name=args.run_name,
                output_path=args.output,
                show=not args.no_show,
            )

        print("Done!")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
