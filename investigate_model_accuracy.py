import  pandas as pd


data = pd.read_excel("tuss_CA_sample_17032026 Testing - SG Additions.xlsx")
data_to_analyse = data[data["Correct Match "].notna()]
print()
# todo apply RAG to the data see if can label
