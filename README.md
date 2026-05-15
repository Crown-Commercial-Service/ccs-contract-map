# ccs-contract-map


This repository provides a tool to automatically label contract descriptions using the CCS categories. It leverages a Large Language Model (LLM) to classify contract descriptions into predefined categories accurately and consistently.

## Project Structure

```
ccs-contract-map/
├── src/                           # Source code
│   ├── core/                      # Core classification modules
│   │   ├── classification_v1.py   # Version 1 (SystemMessage/HumanMessage)
│   │   └── classification_v2.py   # Version 2 (string concatenation)
│   └── api/                       # FastAPI endpoints
│       ├── v1_endpoint.py         # API for version 1
│       └── v2_endpoint.py         # API for version 2
├── prompts/                       # System prompts
│   ├── system_prompts.py          # Python prompt definitions
│   ├── new_system_prompt.txt      # Text-based prompt
│   └── contractmap_prompt_with_descriptions.txt
├── evaluation/                    # Evaluation scripts
│   ├── run_evaluation.py          # Unified evaluation CLI (v1 or v2)
│   └── prompt_engineering_experiment.ipynb
├── utils/                         # Utility modules
│   └── file_io/                  # File I/O utilities
│       └── file_to_string.py
├── data/                          # Data files
│   ├── input/                    # Input datasets
│   └── results/                  # Evaluation results
└── tests/                        # Unit tests
```

## Features

- Uses a gpt-4.1-mini LLM for classification
- There are 2 LLM architectures: Version 1 (in `src/core/classification_v1.py`) and Version 2 (in `src/core/classification_v2.py`)
- Version 1 uses role‑tagged messages (SystemMessage + HumanMessage) so instructions are treated as high‑priority and
protected from user input, whereas Version 2 sends one raw string with specified newlines that mixes instructions with content.
- The LLM ran on 74 descriptions: Version 1 got accuracy of 87.67123287671232% and
Version 2 got accuracy 89.04109589041096%. However, Version 1
is safer because it uses a SystemMessage that separates instructions from user input,
so the model treats those instructions as higher priority and they are harder for user text to override.
This reduces the risk of prompt‑injection.

Note: According to Microsoft, it is not possible to obtain 100% deterministic
results from LLMs. When you repeat an experiment, the model’s outputs
can vary by a few percentage points. This variability occurs because many queries are subjective
or admit multiple valid answers, so the model may produce different responses on different runs.
Setting temperature to 0 reduces randomness but does not guarantee identical outputs. For more information, see:
https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/reproducible-output?tabs=pyton

recent experiment of LLM version 2 system prompt vs system prompt version 2 can be seen:
here: https://docs.google.com/document/d/1faUwE-W7Eh3n6qg4sblHMjMtkmziJCG9/edit#heading=h.vigkhlj1brjf
The experiment was ran using `evaluation/run_demo_v2.py`

## How It Works

Contractmap is a hybrid keyword + LLM system. When a contract description is passed in, the following happens:
1. Keyword Matching: the description is searched for the occurrence of keywords that are relevant to each category. If enough keywords are found for a given category (as defined by the threshold value), and there is not a similar number of keywords for another category (with "similar" defined by the margin value), that category is chosen as the match for the description.
2. LLM (optional): if there is no single category that achieves a high enough keyword matching score, the description is passed to an LLM, which uses its understanding of natural language to assign the contract to a GCA category.
Once this process finishes, the system returns a single CCS category name.


## Developer Tooling (Pre-commit, Ruff, pytest)

This project uses:

- [pre-commit](https://pre-commit.com/) for running checks automatically before each commit.
- [Ruff](https://docs.astral.sh/ruff/) for fast linting.
- [pytest](https://docs.pytest.org/) for unit testing.

### Install tooling

If you already installed dependencies from `requirements.txt`, install the remaining developer tools:

```bash
python -m pip install pre-commit ruff
```

Or install all at once:

```bash
python -m pip install -r requirements.txt pre-commit ruff
```

### Set up pre-commit hooks

Install hooks locally:

```bash
pre-commit install
```

Run all hooks manually across the repository:

```bash
pre-commit run --all-files
```

### Run Ruff and pytest manually

Run Ruff:

```bash
ruff check .
```

Run tests:

```bash
pytest -q
```

## Evaluation

This section describes how to evaluate the contract mapping model using ground truth data and MLflow tracking.

### Prerequisites

1. Install the required dependencies:
```bash
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

2. Set up Azure MLflow environment variables in `.env`:
```bash
MLFLOW_TRACKING_URI=azureml://...
MLFLOW_EXPERIMENT_NAME=ContractMap-Evaluation
```

3. Authenticate with Azure:
```bash
az login
```

### Step 1: Process the Truthset

Before running evaluation, prepare your ground truth data using the `process_truthset.py` script. This script:
- Cleans and normalizes category names (e.g., converts '&' to 'and', standardizes plural forms)
- Removes rows with missing required data
- Splits data into train and test sets with stratified sampling

**Usage:**

```bash
python src/utils/process_truthset.py \
  --input data/input/your_truthset.xlsx \
  --train-ratio 0.8
```

**Parameters:**
- `--input`: Path to input Excel file with columns: `Title`, `Description`, `Category` (required)
- `--train-ratio`: Proportion of data for training set, between 0.0 and 1.0 (required)

**Example:**

```bash
# Split into 80% train, 20% test
python src/utils/process_truthset.py \
  --input data/input/your_truthset.xlsx \
  --train-ratio 0.8
```

This will:
1. Clean and normalize the input file (overwrites original)
2. Create two TSV files:
   - `your_truthset_train.tsv` (80% of data)
   - `your_truthset_test.tsv` (20% of data)

### Step 2: Run Evaluation with One Configuration

Use the `run_eval.py` script to evaluate the model on your test set. This script:
- Runs the hybrid keyword + LLM classifier on each contract description
- Calculates accuracy metrics
- Logs results to Azure MLflow
- Saves predictions and wrong results to CSV/JSON files

**Usage:**

```bash
python eval/run_eval.py \
  --truthset data/input/your_test_set.tsv \
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

### Step 3: Run Evaluation across Multiple Configurations

To find the optimal configuration, use the `eval/optimise_parameters.sh` file, which runs a grid search across multiple combinations of the threshold and margin parameters. You can run the file directly through the terminal:

```bash
bash eval/optimise_parameters.sh
```

### Step 4: Visualize Results

After running multiple evaluations, use the `visualise_experiments.py` script to visualize the optimization results. This script fetches all runs from an MLflow experiment and generates plots showing how accuracy varies with threshold and margin parameters.

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
