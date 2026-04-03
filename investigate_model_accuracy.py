import  pandas as pd

from src.core.classification_v3_mix_v5 import keywords_and_llm
from src.core.classification_v3 import contract_mapper_v3
import ast

data = pd.read_excel("AI Catrgorisation Testing Notes2.xlsx")
drop_1 = data.iloc[0:8].index# remove rows where it does not matter what label the model gives
drop_2 = data.iloc[170:181].index # remove rows where it does not matter what label the model gives

all_to_drop = drop_1.union(drop_2)
new_data = data.drop(all_to_drop)


data_to_analyse = new_data[new_data["Correct Match "].notna()].iloc[0:669]


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
data_to_analyse.to_excel("new_AI_results.xlsx", index=False)
accuracy = data_to_analyse["AI_CategoryMatchV3"] == data_to_analyse["Correct Match "]

correct_count = accuracy.sum()
total_count = len(accuracy)
old_model_correct_df = data_to_analyse[data_to_analyse["AI_CategoryMatch"] == data_to_analyse["Correct Match "]]
print(f"Total Analyzed: {total_count}")
print(f"Correct Matches: {correct_count}, Old model total correct matches: {len(old_model_correct_df)/total_count*100}%")
print(f"Correct Matches %: {(correct_count/total_count)*100}, Old model total correct matches%: {len(old_model_correct_df)/total_count*100}%")