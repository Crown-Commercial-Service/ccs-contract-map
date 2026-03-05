from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
import os
from python_system_prompt import system_prompt_v2

load_dotenv()

SYSTEM_PROMPT = system_prompt_v2()

llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_deployment=os.getenv("DEPLOYMENT_NAME"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0.0,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    seed=42,
    max_tokens=6,
)


async def contract_mapper_v2(user_contract_description, llm=llm, system_prompt=SYSTEM_PROMPT):
    input_prompt = f"\n user input:{user_contract_description} "
    response = llm.invoke(system_prompt + input_prompt)

    return response.content
