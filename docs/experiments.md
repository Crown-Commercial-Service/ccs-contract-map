# Experiments

## Current System Accuracy

87.67%

## Experiment Details

### Dataset

We are quantifying performance using a human-generated truthset of 73 pairs of contract descriptions and their associated categories. This covers a variety of different categories, and includes examples known to fail using other categorisation approaches e.g. keyword detection.

### Method

We compared the performance of two prompts, version 1 (from `app.py`) and version 2 (from `contract_mapping_v2.py`). We define accuracy as the % of LLM-generated categories that match the human-labelled category.

To run the experiment yourself:

1. Install the environment as a jupyter kernel by running `poetry run python -m ipykernel install --user --name="ccs-contract-map"`
2. Launch a jupyter lab session by running `poetry run jupyter lab`
3. In the jupyter lab landing page that launches in your browser, select the kernel `ccs-contract-map`
4. Open the notebook `prompt_engineering_experiment.ipynb`

**Note:** if your browser doesn't automatically load the jupyter lab landing page, you may need to follow the link that is displayed in the terminal instead

### Results

Version 1 was 87.67% accurate, and version 2 was 89.04% accurate. However, the version 1 is safer because it uses a `SystemMessage` to separate instructions from user input, so the model treats those instructions as higher priority and they are harder for user text to override. See [here](https://docs.google.com/document/d/1faUwE-W7Eh3n6qg4sblHMjMtkmziJCG9/edit#heading=h.vigkhlj1brjf) for a static version of the experiment results.