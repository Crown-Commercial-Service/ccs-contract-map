# ccs-contract-map


This repository provides a tool to automatically label contract descriptions using the CCS categories. It leverages a Large Language Model (LLM) to classify contract descriptions into predefined categories accurately and consistently.

## Features

- Uses a gpt-4.1-mini LLM for classification
- Implements two prompt styles to improve accuracy and stability
- The most reliable and stable version, as determined through experimentation, is embedded in `app.py` which
  achieved an accuracy of 89.65517241379311%% and model found `contract_mapping_v2.py` had accuracy of 82.75862068965517%%


## How It Works

1. Input: A contract description text
2. Processing: The LLM, invoked in `app.py`, applies the best prompt style identified during testing
3. Output: A single CCS category label that best fits the contract description
Note: when running the experiment_mapping.py do know that LLMs are stochastic in nature and we tried
to keep as deterministic as possible by setting temperature=0 and other parameters such as
opp=1, frequencypenalty=0 and presence_penalty=0 reduce variability, but results can be few percentage
different due to how LLMs are built.

## How to get to run on own pc

1. install libraries seen in `pyproject.toml` file
2. create a `.env` file a load your azure credentials
3. run any of the files in the repo