# ccs-contract-map 


This repository provides a tool to automatically label contract descriptions using the CCS categories. It leverages a Large Language Model (LLM) to classify contract descriptions into predefined categories accurately and consistently.

## How It Works

Contractmap is a hybrid keyword + LLM system. When a contract description is passed in, the following happens:
1. Keyword Matching: the description is searched for the occurrence of keywords that are relevant to each category. If enough keywords are found for a given category (as defined by the threshold value), and there is not a similar number of keywords for another category (with "similar" defined by the margin value), that category is chosen as the match for the description.
2. LLM (optional): if there is no single category that achieves a high enough keyword matching score, the description is passed to an LLM, which uses its understanding of natural language to assign the contract to a GCA category.
Once this process finishes, the system returns a single CCS category name.

## How To Install Locally

### Python

The system and its unit tests are all written in python. To install it, first ensure that Python is installed on your system, and then follow these steps:

1. Create a venv:
```
python -m venv venv
```
2. Load the venv:
```
source venv/bin/activate
```
3. Update pip:
```
python -m pip install --upgrade pip
```
4. Install the dependencies:
```
python -m pip install -r requirements.txt
```

### TypeScript

Functional tests are written in TypeScript and run through Playwright. To install the TypeScript environment, first ensure that node.js is installed on your system, and then run:
```
npm install
```

## Developer Tooling (Pre-commit, Ruff, pytest, playwright)

This project uses:

- [pre-commit](https://pre-commit.com/) for running checks automatically before each commit.
- [Ruff](https://docs.astral.sh/ruff/) for fast linting.
- [pytest](https://docs.pytest.org/) for unit testing.
- [playwright](https://playwright.dev/) for functional testing.

### Set up pre-commit hooks

Install hooks locally:

```bash
pre-commit install
```

Run all hooks manually across the repository:

```bash
pre-commit run --all-files
```

### Run Ruff and tests manually

Run Ruff:

```bash
ruff check .
```

Run unit tests:

```bash
pytest -q
```

Run functional tests:

```bash
npx playwright test
```

## Evaluation & Optimisation

This section describes how to evaluate and optimise the contract mapping model using ground truth data and MLflow tracking.

### Prerequisites

1. Install the required dependencies:
```bash
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

2. Set up environment variables in `.env`:
```bash
# Azure OpenAI (required for keyword extraction and LLM classification)
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_KEY=<your-api-key>
DEPLOYMENT_NAME=<your-deployment-name>
AZURE_OPENAI_API_VERSION=2024-02-01

# Azure MLflow (required for evaluation tracking)
MLFLOW_TRACKING_URI=azureml://...
MLFLOW_EXPERIMENT_NAME=ContractMap-Evaluation
```

3. Authenticate with Azure:
```bash
az login
```

### Run Evaluation

Use the `run_eval.py` script to evaluate the model on your truthset. This script:
- Runs the hybrid keyword + LLM classifier on each contract description
- Calculates accuracy metrics
- Logs results to Azure MLflow
- Saves predictions and wrong results to CSV/JSON files
*NOTE*: your truthset must have the following column headers: `Title`, `Description`, `Category`

**Usage:**

```bash
python eval/run_eval.py \
  --truthset data/inputs/your_test_set.tsv \
  --threshold 10 \
  --margin 0 \
  --prompt system_prompt_v2.md \
  --mlflow-tracking-uri "azureml://..." \
  --mlflow-experiment-name "ContractMap-Evaluation" \
  --mlflow-run-name "test-run-001"
```

**Parameters:**
- `--truthset`: Path to truthset file (CSV, TSV, or Excel) with `Title`, `Description`, `Category` columns
- `--output`: Optional output CSV path (defaults to `data/results/eval_keywords_llm_t{threshold}_m{margin}.csv`)
- `--threshold`: Keyword threshold for classification (default: 10)
- `--margin`: Margin parameter for classification (default: 0)
- `--prompt`: System prompt file name from `prompts/` directory (default: `system_prompt_v2.md`)
- `--list-prompts`: List available prompt files and exit
- `--mlflow-tracking-uri`: Azure MLflow tracking URI (or set `MLFLOW_TRACKING_URI` env var)
- `--mlflow-experiment-name`: MLflow experiment name (optional)
- `--mlflow-run-name`: MLflow run name (optional)

**Example:**

```bash
# List available prompts
python eval/run_eval.py --list-prompts

# Run evaluation with default parameters
python eval/run_eval.py \
  --truthset data/input/your_truthset_test.tsv \
  --threshold 10 \
  --margin 0 \
  --prompt system_prompt_v2.md

# Run evaluation with custom parameters and MLflow tracking
python eval/run_eval.py \
  --truthset data/input/your_truthset_test.tsv \
  --output data/results/my_evaluation.csv \
  --threshold 5 \
  --margin 1 \
  --prompt keyword_system_prompt_v2.md \
  --mlflow-experiment-name "ContractMap-PromptOptimization" \
  --mlflow-run-name "threshold-5-margin-1"
```

Files created:
- `data/results/eval_keywords_llm_t10_m0.csv`: Predictions for all samples
- `data/results/eval_keywords_llm_t10_m0_wrong_results.json`: Detailed information about incorrect predictions

**MLflow Tracking:**

The evaluation script logs the following to MLflow:
- **Parameters**: truthset path, threshold, margin, prompt name, classifier version
- **Metrics**: accuracy percentage, correct/wrong prediction counts, evaluation duration
- **Artifacts**: results CSV, wrong results JSON, system prompt file

View results in Azure ML Studio or query programmatically.

### Optimise System Configuration

This project uses [DVC (Data Version Control)](https://dvc.org/) to orchestrate a reproducible machine learning pipeline for finding the optimal configuration for contractmap. The pipeline automates data processing, keyword extraction, hyperparameter optimization, and results visualization.

### Pipeline Overview

The pipeline consists of four stages:

1. **process_data**: Cleans and normalizes the truthset data, then splits it into train and test sets
2. **extract_keywords**: Extracts semantic anchors (keywords) from the training data using LLM
3. **optimize_params**: Runs a grid search across threshold and margin parameters, logging results to MLflow
4. **visualize**: Generates visualization plots of the optimization results

To see how these stages are linked together, run:

```
dvc dag
```

### Running the Full Pipeline

To execute the entire pipeline from start to finish:

```bash
# Run all stages
dvc repro
```

The pipeline will:
1. Process the input Excel file and create train/test splits
2. Extract semantic keywords from training data
3. Run 21 evaluations (7 thresholds × 3 margins) and log to MLflow
4. Generate a 3D optimization surface plot

**Note**: This could take hours to run, depending on the size of the optimisation dataset and on LLM API response times.

### Changing the Pipeline Configuration

All pipeline parameters are centralized in `params.yaml`. To modify parameters:

1. Edit `params.yaml` with your desired values
2. Run `dvc repro` to re-execute affected stages

### Visualising Results

After running the DVC pipeline, if you want to customise the visualisation pf metrics, you can use the `visualise_experiments.py` script directly. This script fetches all runs from an MLflow experiment and generates plots showing how accuracy varies with threshold and margin parameters.

**Usage:**

```bash
python eval/visualise_experiments.py \
  --mlflow-tracking-uri "azureml://..." \
  --mlflow-experiment-name "ContractMap-KeywordLLM-Evaluation" \
  --plot-type surface
```

**Parameters:**
- `--mlflow-tracking-uri`: Azure MLflow tracking URI (or set `MLFLOW_TRACKING_URI` env var)
- `--mlflow-experiment-name`: MLflow experiment name (default: `ContractMap-KeywordLLM-Evaluation`)
- `--plot-type`: Plot type - `surface` for 3D surface plot or `scatterplot` for 2D scatter plot (default: `surface`)
- `--output`: Optional output path to save the plot (e.g., `optimization_surface.png`)
- `--no-show`: Don't display the plot interactively (useful for headless environments)

**Examples:**

```bash
# Generate 3D surface plot (default)
python eval/visualise_experiments.py

# Generate 2D scatter plot
python eval/visualise_experiments.py --plot-type scatterplot

# Save plot to file without displaying it
python eval/visualise_experiments.py \
  --plot-type surface \
  --output data/results/optimization_surface.png \
  --no-show

# Visualize results from a specific experiment
python eval/visualise_experiments.py \
  --mlflow-experiment-name "ContractMap-PromptOptimization" \
  --plot-type scatterplot \
  --output data/results/prompt_optimization.png
```