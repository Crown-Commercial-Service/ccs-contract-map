from app import contract_mapper
import pandas as pd
from pathlib import Path
from contract_mapping_v2 import contract_mapper_v2
"""
This script is used to check how well LLM classifies
using csv containing  examples of contract description.
Here system prompts are compared to see which LLM architecture
to go with. From experiment the LLM in app.py is the most
stable and accurate.
"""


df = pd.read_csv(Path.cwd() / "AI Category Mapping - Category Desc Examples_new.csv")
df = df.dropna(subset=['Description']).copy() #in case anyone forgets to add a description
df = df.reset_index(drop=True)

list_descriptions = df["Description"].values.tolist()
list_category = df["Category"].values.tolist()

count_correct = 0
list_results = []
count_correct2 = 0
list_results2 = []
for description, category in zip(list_descriptions, list_category):
    system_prompt_file_location = Path.cwd() / "new_system_prompt.txt"
    result = contract_mapper(system_prompt_file_location= system_prompt_file_location,user_contract_description=description)
    list_results.append(result)
    print(f"V1 actual:{category}  AI:{result}, {category in result}")
    if category == result:
        count_correct += 1
    result2 = contract_mapper_v2(user_contract_description=description)
    list_results2.append(result2)
    print(f"V2 actual:{category}  AI:{result2}, {category in result2}")
    if category == result2:
        count_correct2 += 1
    print()


print(f" V1 accuracy:{(count_correct/len(list_descriptions))*100}%")
print(f" V2 accuracy:{(count_correct2/len(list_descriptions))*100}%")
new_df = df[["Category", "Description"]].copy()
new_df["LLM Version1"] = list_results
new_df["LLM Version2"] = list_results2
new_df.to_csv("AI_results.csv")
print("experiment completed")