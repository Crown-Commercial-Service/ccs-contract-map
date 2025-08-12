# ccs-contract-map


This repository provides a tool to automatically label contract descriptions using the CCS categories. It leverages a Large Language Model (LLM) to classify contract descriptions into predefined categories accurately and consistently.

## Features

- Uses a gpt-4.1-mini LLM for classification
- Implements two prompt styles to improve accuracy and stability
- The most reliable and stable version, as determined through experimentation, is embedded in `app.py` which
  achieved an accuracy of 89.65517241379311% and model found `contract_mapping_v2.py` had accuracy of 86.20689655172413%


## How It Works

1. Input: A contract description text
2. Processing: The LLM, invoked in `app.py`, applies the best prompt style identified during testing
3. Output: A single CCS category label that best fits the contract description
note: the best prompt is the text file in called new_system_prompt.txt, a python system prompt
was created to see if formatting impacts llm results which it does. It seems like specifying
to LLM what part of the prompt is a system prompt and what part is from the user
allows the results to be more reproducible(ran experiment 20x and got same results using `app.py`) this is seen app.py `prompt = [SystemMessage(content=system_prompt_string) , HumanMessage(content=user_contract_description.strip())]`


## How to get to run on own pc

1. install libraries seen in `pyproject.toml` file
2. create a `.env` file a load your azure credentials
3. run any of the python files in the repo