# ccs-contract-map


This repository provides a tool to automatically label contract descriptions using the CCS categories. It leverages a Large Language Model (LLM) to classify contract descriptions into predefined categories accurately and consistently.

## Features

- Uses a gpt-4.1-mini LLM for classification
- There are 2 llm architecture one exists in `app.py` and the other one  in`contract_mapping_v2.py`, the 
difference is `app.py` uses role‑tagged messages (SystemMessage + HumanMessage) so instructions are treated as high‑priority and 
protected from user input, whereas the LLM in `contract_mapping_v2.py`sends one raw string with specified newlines that mixes instructions with content.
- The LLM ran on 74 descriptions the LLM version 1  from `app.py` got accuracy of 87.67123287671232% and
 LLM version 2 from `contract_mapping_v2.py` got accuracy 89.04109589041096%. However, the LLM in `app.py`
is safer because the LLM in `app.py`uses a SystemMessage separates instructions from user input, 
so the model treats those instructions as higher priority and they are harder for user text to override. 
This reduces the risk of prompt‑injection.

Note: According to Microsoft, it is not possible to obtain 100% deterministic
results from LLMs. When you repeat an experiment, the model’s outputs
can vary by a few percentage points. This variability occurs because many queries are subjective 
or admit multiple valid answers, so the model may produce different responses on different runs.
Setting temperature to 0 reduces randomness but does not guarantee identical outputs. For more information, see: 
https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/reproducible-output?tabs=pyton


## How It Works

1. Input:LLM is given a contract description text
2. Processing: LLM uses the system prompt to understand how to categorise the given contract description
3. Output: A single CCS category label that best fits the contract description is outputted by LLM


## How to get to run on own pc

1. go into the repo folder in your command-line using `cd`
2. run command `poetry install` (make sure you have poetry on your pc)
3. create a `.env` file to load your azure credentials(name your credentials as shown below):
   - AZURE_OPENAI_API_VERSION
   - AZURE_OPENAI_ENDPOINT
   - AZURE_OPENAI_KEY
   - DEPLOYMENT_NAME
4. Make sure you have a AI Category Mapping csv that contain descriptions and what categories, make sure
the columns are labelled as `Description` and `Category`. Please name the csv file `AI Category Mapping - Category Desc Examples_new.csv`
5. to run experiment you can run on your IDE the file `experiment_mapping.py` which will output a csv called `AI_results.csv`

