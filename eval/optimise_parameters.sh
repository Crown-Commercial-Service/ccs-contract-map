#!/bin/bash

# Script to run parameter optimization for contract mapping evaluation
# Tests all combinations of threshold and margin parameters

set -e  # Exit on error

# Define parameter ranges
THRESHOLDS=(1 2 3 5 10 25 50)
MARGINS=(1 5 10)

# Get the repository root (two levels up from src/utils)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EVALUATION_SCRIPT="$REPO_ROOT/eval/run_eval.py"
TRUTHSET_PATH="$REPO_ROOT/new_AI_results_for_Jasmine.xlsx"

# Verify the evaluation script exists
if [[ ! -f "$EVALUATION_SCRIPT" ]]; then
    echo "Error: Evaluation script not found at $EVALUATION_SCRIPT"
    exit 1
fi

# Count total runs
TOTAL_RUNS=$((${#THRESHOLDS[@]} * ${#MARGINS[@]}))
CURRENT_RUN=0

echo "Starting parameter optimization sweep"
echo "Total combinations to test: $TOTAL_RUNS"
echo "Thresholds: ${THRESHOLDS[*]}"
echo "Margins: ${MARGINS[*]}"
echo "----------------------------------------"

# Iterate through all combinations
for threshold in "${THRESHOLDS[@]}"; do
    for margin in "${MARGINS[@]}"; do
        CURRENT_RUN=$((CURRENT_RUN + 1))
        
        echo ""
        echo "Run $CURRENT_RUN/$TOTAL_RUNS: threshold=$threshold, margin=$margin"
        echo "----------------------------------------"
        
        # Create a descriptive run name for MLflow
        RUN_NAME="t${threshold}_m${margin}"
        
        # Run evaluation with current parameters
        python "$EVALUATION_SCRIPT" \
            --truthset "$TRUTHSET_PATH" \
            --threshold "$threshold" \
            --margin "$margin" \
            --mlflow-run-name "$RUN_NAME"
        
        echo "Completed: $RUN_NAME"
    done
done

echo ""
echo "========================================="
echo "Parameter optimization sweep completed!"
echo "Total runs: $TOTAL_RUNS"
echo "Check MLflow UI for results comparison"
echo "========================================="
