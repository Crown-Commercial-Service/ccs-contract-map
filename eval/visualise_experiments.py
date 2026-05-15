import argparse
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent


def _get_mlflow_module() -> Any | None:
    """Import Azure MLflow module (azureml-mlflow extends standard mlflow)."""
    try:
        import importlib

        return importlib.import_module("mlflow")
    except ModuleNotFoundError:
        return None


def fetch_experiment_runs(
    mlflow_tracking_uri: str | None = None,
    mlflow_experiment_name: str = "ContractMap-KeywordLLM-Evaluation",
) -> pd.DataFrame:
    """
    Fetch all runs from the specified MLflow experiment.

    Args:
        mlflow_tracking_uri: Azure MLflow tracking URI
        mlflow_experiment_name: MLflow experiment name

    Returns:
        DataFrame with columns: threshold, margin, accuracy_percent
    """
    mlflow_module = _get_mlflow_module()
    if mlflow_module is None:
        raise ModuleNotFoundError(
            "Azure MLflow is not installed. Install with 'pip install azureml-mlflow' "
            "and authenticate using 'az login'."
        )

    # Configure MLflow
    tracking_uri = mlflow_tracking_uri or os.getenv("MLFLOW_TRACKING_URI")
    if not tracking_uri:
        raise ValueError(
            "MLflow tracking URI is required. "
            "Set --mlflow-tracking-uri or MLFLOW_TRACKING_URI."
        )

    mlflow_module.set_tracking_uri(tracking_uri)

    # Get experiment
    experiment = mlflow_module.get_experiment_by_name(mlflow_experiment_name)
    if experiment is None:
        raise ValueError(
            f"Experiment '{mlflow_experiment_name}' not found. "
            f"Please check the experiment name and try again."
        )

    print(
        f"Found experiment: {mlflow_experiment_name} (ID: {experiment.experiment_id})"
    )

    # Search all runs for this experiment
    runs = mlflow_module.search_runs(
        experiment_ids=[experiment.experiment_id],
        output_format="pandas",
    )

    if runs.empty:
        raise ValueError(
            f"No runs found for experiment '{mlflow_experiment_name}'. "
            f"Please run some experiments first."
        )

    print(f"Found {len(runs)} runs")

    # Extract relevant columns
    data = []
    for _, run in runs.iterrows():
        # Extract parameters and metrics
        threshold = run.get("params.threshold")
        margin = run.get("params.margin")
        accuracy_percent = run.get("metrics.accuracy_percent")

        # Only include runs that have all required values
        if (
            threshold is not None
            and margin is not None
            and accuracy_percent is not None
        ):
            data.append(
                {
                    "threshold": float(threshold),
                    "margin": float(margin),
                    "accuracy_percent": float(accuracy_percent),
                }
            )

    if not data:
        raise ValueError(
            "No runs found with required parameters (threshold, margin) and metrics (accuracy_percent). "
            "Please ensure your runs logged these values."
        )

    df = pd.DataFrame(data)
    print(f"Extracted {len(df)} runs with complete data")
    print(f"\nThreshold range: {df['threshold'].min()} - {df['threshold'].max()}")
    print(f"Margin range: {df['margin'].min()} - {df['margin'].max()}")
    print(
        f"Accuracy range: {df['accuracy_percent'].min():.2f}% - {df['accuracy_percent'].max():.2f}%"
    )

    return df


def plot_optimization_surface(
    df: pd.DataFrame,
    output_path: Path | None = None,
    show_plot: bool = True,
) -> None:
    """
    Generate a 3D surface plot of the optimization results.

    Args:
        df: DataFrame with columns threshold, margin, accuracy_percent
        output_path: Optional path to save the plot
        show_plot: Whether to display the plot interactively
    """
    # Prepare data for surface plot
    threshold_values = sorted(df["threshold"].unique())
    margin_values = sorted(df["margin"].unique())

    # Create a grid
    X, Y = np.meshgrid(threshold_values, margin_values)
    Z = np.zeros_like(X, dtype=float)

    # Fill the grid with accuracy values
    for i, margin in enumerate(margin_values):
        for j, threshold in enumerate(threshold_values):
            # Find the accuracy for this combination
            match = df[(df["threshold"] == threshold) & (df["margin"] == margin)]
            if not match.empty:
                Z[i, j] = match["accuracy_percent"].values[0]
            else:
                Z[i, j] = np.nan

    # Create the 3D plot
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection="3d")

    # Plot surface
    surf = ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.8, edgecolor="none")

    # Add scatter points for actual data points
    ax.scatter(
        df["threshold"],
        df["margin"],
        df["accuracy_percent"],
        c="red",
        marker="o",
        s=50,
        alpha=0.6,
        label="Actual runs",
    )

    # Labels and title
    ax.set_xlabel("Threshold", fontsize=12, labelpad=10)
    ax.set_ylabel("Margin", fontsize=12, labelpad=10)
    ax.set_zlabel("Accuracy (%)", fontsize=12, labelpad=10)
    ax.set_title(
        "Contract Classification Optimization Surface\n(Threshold vs Margin vs Accuracy)",
        fontsize=14,
        pad=20,
    )

    # Add colorbar
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label="Accuracy (%)")

    # Add legend
    ax.legend(loc="upper left")

    # Find and annotate best result
    best_idx = df["accuracy_percent"].idxmax()
    best_row = df.loc[best_idx]
    ax.text(
        best_row["threshold"],
        best_row["margin"],
        best_row["accuracy_percent"],
        f'  Best: {best_row["accuracy_percent"]:.2f}%\n  (t={best_row["threshold"]:.0f}, m={best_row["margin"]:.0f})',
        fontsize=10,
        color="black",
        weight="bold",
    )

    plt.tight_layout()

    # Save if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"\nPlot saved to {output_path}")

    # Show plot if requested
    if show_plot:
        plt.show()


def plot_scatterplot(
    df: pd.DataFrame,
    output_path: Path | None = None,
    show_plot: bool = True,
) -> None:
    """
    Generate a scatterplot of the optimization results.

    Args:
        df: DataFrame with columns threshold, margin, accuracy_percent
        output_path: Optional path to save the plot
        show_plot: Whether to display the plot interactively
    """
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Create scatter plot with accuracy as color
    scatter = ax.scatter(
        df["threshold"],
        df["margin"],
        c=df["accuracy_percent"],
        cmap="viridis",
        s=200,
        alpha=0.8,
        edgecolors="black",
        linewidth=1.5,
    )

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, label="Accuracy (%)")
    cbar.ax.tick_params(labelsize=10)

    # Find and annotate best result
    best_idx = df["accuracy_percent"].idxmax()
    best_row = df.loc[best_idx]
    ax.annotate(
        f'Best: {best_row["accuracy_percent"]:.2f}%\n(t={best_row["threshold"]:.0f}, m={best_row["margin"]:.0f})',
        xy=(best_row["threshold"], best_row["margin"]),
        xytext=(10, 10),
        textcoords="offset points",
        fontsize=11,
        weight="bold",
        bbox=dict(
            boxstyle="round,pad=0.5", facecolor="yellow", alpha=0.7, edgecolor="black"
        ),
        arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0", lw=2),
    )

    # Set labels and title
    ax.set_xlabel("Threshold", fontsize=14, weight="bold")
    ax.set_ylabel("Margin", fontsize=14, weight="bold")
    ax.set_title(
        "Contract Classification Optimization Results\n(Threshold vs Margin, colored by Accuracy)",
        fontsize=16,
        weight="bold",
        pad=20,
    )

    # Add grid for readability
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    # Adjust tick label sizes
    ax.tick_params(axis="both", labelsize=11)

    plt.tight_layout()

    # Save if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"\nPlot saved to {output_path}")

    # Show plot if requested
    if show_plot:
        plt.show()


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Visualize MLflow experiment results as optimization plots."
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
        default="ContractMap-KeywordLLM-Evaluation",
        help="Azure MLflow experiment name (default: ContractMap-KeywordLLM-Evaluation).",
    )
    parser.add_argument(
        "--plot-type",
        type=str,
        choices=["surface", "scatterplot"],
        default="surface",
        help="Type of plot to generate: 'surface' for 3D surface plot, 'scatterplot' for 2D scatterplot (default: surface).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path for saving the plot (e.g., optimization_surface.png).",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Don't display the plot interactively (useful for headless environments).",
    )
    return parser


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Fetch experiment runs
    df = fetch_experiment_runs(
        mlflow_tracking_uri=args.mlflow_tracking_uri,
        mlflow_experiment_name=args.mlflow_experiment_name,
    )

    # Generate plot based on selected type
    if args.plot_type == "surface":
        plot_optimization_surface(
            df=df,
            output_path=args.output,
            show_plot=not args.no_show,
        )
    elif args.plot_type == "scatterplot":
        plot_scatterplot(
            df=df,
            output_path=args.output,
            show_plot=not args.no_show,
        )

    # Print summary statistics
    print("\n--- Summary Statistics ---")
    print(f"Total runs analyzed: {len(df)}")
    print("\nBest configuration:")
    best_idx = df["accuracy_percent"].idxmax()
    best_row = df.loc[best_idx]
    print(f"  Threshold: {best_row['threshold']:.0f}")
    print(f"  Margin: {best_row['margin']:.0f}")
    print(f"  Accuracy: {best_row['accuracy_percent']:.2f}%")


if __name__ == "__main__":
    main()
