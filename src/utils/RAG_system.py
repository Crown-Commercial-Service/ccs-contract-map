from CCS_web_api.api import fetch_all_ccs_frameworks
from langchain_openai import AzureOpenAIEmbeddings
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv
import hashlib
from src.utils.llm_data_summariser import  summarise_llm

load_dotenv()

BASE_URL = "https://www.crowncommercial.gov.uk/api/frameworks"
COLUMNS_TO_CLEAN = ("description", "summary", "benefits", "how_to_buy", "keywords")
extra_context_data = fetch_all_ccs_frameworks(base_url=BASE_URL, columns_to_clean=COLUMNS_TO_CLEAN)
extra_context_data = extra_context_data[extra_context_data["status"] == "Live"]

embed = AzureOpenAIEmbeddings(
    model=os.getenv("EMBEDDING_MODEL_NAME"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("EMBEDDING_ENDPOINT"),
    api_version=os.getenv("EMBEDDING_API_VERSION"),
)

client = SearchClient(
    endpoint=os.getenv("VECTOR_STORE_ENDPOINT"),
    index_name=os.getenv("VECTOR_STORE_INDEX"),
    credential=AzureKeyCredential(os.getenv("VECTOR_STORE_KEY")),
)


for index, row in extra_context_data.iterrows():
    print(index)
    raw_text = f"""
    Framework Title: {row['title']}
    Framework Code: {row['rm_number']}
    Category: {row['category']}
    Pillar: {row['pillar']}
    Summary: {row['summary']}
    Detailed Description: {row['description']}
    Specific Services/Lots: {row['lots']}
    Keywords: {row['keywords']}
    """
    summarised_text = summarise_llm(raw_text)
    print(summarised_text)
    id_string = row['title']
    unique_id = hashlib.md5(id_string.encode("utf-8")).hexdigest()
    ccs_label = row["category"]

    embedded_chunk = embed.embed_query(summarised_text)
    docs = [{
        "id":unique_id,
        "ccs_label": ccs_label,
        "label_context": summarised_text,
        "label_context_embedded": embedded_chunk
    }
    ]

    client.upload_documents(documents=docs)
    print("Completed")




