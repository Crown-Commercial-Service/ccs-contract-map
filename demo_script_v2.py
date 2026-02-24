from contract_mapping_v2 import contract_mapper_v2
import pandas as pd
from pathlib import Path

"""
this script demos LLMs shows ability to classify CCS category
by looking at contract description
"""


df = pd.read_csv(Path.cwd() / "AI Category Mapping - Category Desc Examples_new.csv")
df = df.dropna(
    subset=["Description"]
).copy()  # in case anyone forgets to add a description
df = df.reset_index(drop=True)

list_descriptions = df["Description"].values.tolist()
list_category = df["Category"].values.tolist()

count_correct = 0
list_results = []

for description, category in zip(list_descriptions, list_category):
    result = contract_mapper_v2(user_contract_description=description)
    list_results.append(result)
    print(f" actual:{category}  AI:{result}, {category in result}")
    if category == result:
        count_correct += 1
    print()


print(
    f" AI accuracy:{(count_correct/len(list_descriptions))*100}% on {len(list_results)} samples"
)


new_df = df[["Category", "Description"]].copy()
new_df["AI classification"] = list_results

new_df.to_csv("AI_v2_results_optimised.csv")
print("experiment completed")
