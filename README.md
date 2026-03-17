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

1. Input:LLM is given a contract description text
2. Processing: LLM uses the system prompt to understand how to categorise the given contract description
3. Output: A single CCS category label that best fits the contract description is outputted by LLM


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

## How to get to run on own pc

### From the terminal

1. go into the repo folder in your command-line using `cd`
2. create a `.env` file to load your azure credentials (name your credentials as shown below):
   - AZURE_OPENAI_API_VERSION
   - AZURE_OPENAI_ENDPOINT
   - AZURE_OPENAI_KEY
   - DEPLOYMENT_NAME
3. Make sure you have a AI Category Mapping csv that contain descriptions and what categories, make sure
the columns are labelled as `Description` and `Category`. Place this file in `data/input/AI Category Mapping - Category Desc Examples_new.csv`
4. Run the unified evaluation script:
```bash
python evaluation/run_evaluation.py --mapper v2
```
Optional arguments:
- `--truth-set /path/to/truth.csv` to use a different truth set file.
- `--prompt system_prompt_v2.md` to choose a prompt from `prompts/`.
- `--list-prompts` to print available prompt files.

### From a jupyter notebook

1. Install the environment as a jupyter kernel by running `poetry run python -m ipykernel install --user --name="ccs-contract-map"`
2. Launch a jupyter lab session by running `poetry run jupyter lab`
3. In the jupyter lab landing page that launches in your browser, select the kernel `ccs-contract-map`
4. Open the notebook `prompt_engineering_experiment.ipynb`

**Note:** if your browser doesn't automatically load the jupyter lab landing page, you may need to follow the link that is displayed in the terminal instead
