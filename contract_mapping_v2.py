from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
import os
from python_system_prompt import system_prompt

load_dotenv()

SYSTEM_PROMPT = system_prompt()

llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_deployment=os.getenv("DEPLOYMENT_NAME"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0.0,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
)

#When you respond, output ONLY the exact category name shown in single quotes at the start of each category (for example, output 'Energy', NOT 'Energy: National Fuels, Provision of Power Purchase Agreement, Supply of Energy, Water, Wastewater and Ancillary Services.'). No additional text or explanation.
def contract_mapper_v2(user_contract_description, llm=llm):
    input_prompt = f"\n user input:{user_contract_description} "
    response = llm.invoke(SYSTEM_PROMPT + input_prompt)
    final_response = llm.invoke(
    response.content + "\n From the text above what Category was picked, only give the Category to user for example: Energy")
    return final_response.content
