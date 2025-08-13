# ccs-contract-map


This repository provides a tool to automatically label contract descriptions using the CCS categories. It leverages a Large Language Model (LLM) to classify contract descriptions into predefined categories accurately and consistently.

## Features

- Uses a gpt-4.1-mini LLM for classification
- Implements two prompt styles to improve accuracy and stability
- The LLM ran on 74 descriptions the LLM version 1  from `app.py` got accuracy of 86.3013698630137% and
 LLM version 2 from `contract_mapping_v2.py` got accuracy 90.41095890410958%

Note: according to microsoft it is impossible to a 100% deterministic results meaning when you run
the experiment you might get varying results by a few percentage, this is due to LLM facing a query
that is subjective meaning that it believes 2 answers could be right so it will sometimes the 2 
different answers when you run it multiple times. Here is link that speaks on this:
https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/reproducible-output?tabs=pyton


## How It Works

1. Input: A contract description text
2. Processing: The LLM, invoked in `app.py`, applies the best prompt style identified during testing
3. Output: A single CCS category label that best fits the contract description


## How to get to run on own pc

1. go into the repo folder in your command-line using `cd`
2. run command `poetry install` (make sure you have poetry on your pc)
3. create a `.env` file a load your azure credentials
4. Make sure you have the AI Category Mapping csv that contain description and what category, make sure
the columns are labelled as Description and Category. Please name the file `AI Category Mapping - Category Desc Examples_new.csv`
4. to run experiment you can run on your IDE the file `experiment_mapping.py`

## About the LLM contract results

When ru