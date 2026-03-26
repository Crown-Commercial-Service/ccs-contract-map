from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from openai import AsyncAzureOpenAI
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelSettings
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
import os
from dotenv import load_dotenv
from azure.search.documents.models import VectorizedQuery
from langchain_openai import AzureOpenAIEmbeddings
from pathlib import Path

load_dotenv()

DEFAULT_SYSTEM_PROMPT_FILE = (
    Path(__file__).parent.parent.parent / "prompts/system_prompt_v3.md"
)


class ContractMapV3(BaseModel):
    ccs_label: str = Field(description="The chosen category of the contract. If no categories in the RULES match the description, return 'Outside Taxonomy'.")



pydantic_azure_client = AsyncAzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_deployment=os.getenv("DEPLOYMENT_NAME"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)
model = OpenAIChatModel(
    model_name=os.getenv("DEPLOYMENT_NAME"),
    provider=OpenAIProvider(openai_client=pydantic_azure_client),
)

client = SearchClient(
    endpoint=os.getenv("VECTOR_STORE_ENDPOINT"),
    index_name=os.getenv("VECTOR_STORE_INDEX"),
    credential=AzureKeyCredential(os.getenv("VECTOR_STORE_KEY")),
)

embed = AzureOpenAIEmbeddings(
    model=os.getenv("EMBEDDING_MODEL_NAME"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint=os.getenv("EMBEDDING_ENDPOINT"),
    api_version=os.getenv("EMBEDDING_API_VERSION"),
)

def get_rules_from_azure(description):
    """Simple search to get the 'Rule Cards' from your 4 columns."""
    search_client = SearchClient(
        endpoint=os.getenv("VECTOR_STORE_ENDPOINT"),
        index_name=os.getenv("VECTOR_STORE_INDEX"),
        credential=AzureKeyCredential(os.getenv("VECTOR_STORE_KEY"))
    )

    # Convert the user's description into numbers (embedding)
    vector = embed.embed_query(description)
    # Find the top 3 matches in your 'label_context_embedded' column
    vector_query = VectorizedQuery(vector=vector, k_nearest_neighbors=3, fields="label_context_embedded")

    results = search_client.search(
        search_text=None,
        vector_queries=[vector_query],
        select=["ccs_label", "label_context"]  # These are your specific columns
    )

    # Combine the found rules into one string
    rules_text = ""
    for doc in results:
        rules_text += f"\n--- CATEGORY: {doc['ccs_label']} ---\n{doc['label_context']}\n"

    return rules_text


def contract_mapper_v3(contract_description):
    relevant_rules = get_rules_from_azure(contract_description)
    llm = Agent(
        model=model,
        output_type=ContractMapV3,
        model_settings=ModelSettings(temperature=0.0),
    )
    with open(DEFAULT_SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
        raw_prompt_template = f.read()

    prompt = raw_prompt_template.replace(
        "{{contract_description}}", contract_description
    ).replace(
        "{{relevant_rules}}", relevant_rules
    )

    result = llm.run_sync(prompt)
    return result.output.ccs_label


if __name__ == "__main__":
    my_contract = "Network Rail BAPA - Bidston Moss Viaduct : This is for a Basic Asset Protection Agreement on a structure to carry out statutory safety inspection and essential maintenance works. Network Rail is the owner and infrastructure manager of the railway network and as such no alternative suppliers are available."
    label = contract_mapper_v3(my_contract)
    print(f"The Label is: {label}")
