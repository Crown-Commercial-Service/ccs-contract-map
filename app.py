from importlib.metadata import pass_none

from langchain_openai import AzureChatOpenAI
from langchain.chains import ConversationChain
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from dotenv import load_dotenv
import os
from file_engineering.file_to_string import file_to_string_processor
from pathlib import Path

load_dotenv()

system_prompt_file_location = Path.cwd() / "contractmap_prompt_with_descriptions.txt"

system_prompt_string = file_to_string_processor(system_prompt_file_location)


prompt = ChatPromptTemplate.from_messages([SystemMessagePromptTemplate.from_template(system_prompt_string + "{input}")])



llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_deployment=os.getenv("DEPLOYMENT_NAME"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0.0
)


chain = prompt | llm
response = chain.invoke({ "input":"This Contract Award Notice covers electricity and/or gas supply procurement services awarded via the Dynamic Purchasing System (DPS). The DPS is available for use by all contracting authorities within England, Scotland, Wales and Northern Ireland as defined by Regulation 2 of the Public Contracts Regulations 2015 #102. The tender process was managed by Equity Energies."})
print(response.content)
