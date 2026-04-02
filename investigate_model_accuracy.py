import  pandas as pd

from src.core.classification_v3_mix_v5 import keywords_and_llm
import ast

data = pd.read_excel("AI Catrgorisation Testing Notes.xlsx")
data_to_analyse = data[data["Correct Match "].notna()].iloc[0:30]
print(len(data_to_analyse))
# todo apply RAG to the data see if can label
# data_to_analyse["AI_CategoryMatchV3"] =
output = []
for index, row in data_to_analyse.iterrows():
    print("row:",index)

    description = ast.literal_eval(row["ContractDescription"])
    print("contract description:", description["description"])
    contract = f"""
    {row["contract_title"]} : {description["description"]}
    
    """

    result, score = keywords_and_llm(contract)
    output.append(result)
    print("AI:",result ,"Actual:", row["Correct Match "])


data_to_analyse["AI_CategoryMatchV3"] =output
accuracy = data_to_analyse["AI_CategoryMatchV3"] == data_to_analyse["Correct Match "]

correct_count = accuracy.sum()
total_count = len(accuracy)
print(f"Total Analyzed: {total_count}")
print(f"Correct Matches: {correct_count}")