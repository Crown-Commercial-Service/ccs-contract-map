from langchain_openai import AzureChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os
from file_engineering.file_to_string import file_to_string_processor


load_dotenv()



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
    max_tokens=4,
)



def contract_mapper(system_prompt_file_location, user_contract_description, llm=llm):
    """ This function reads a description of a contract and labels it.

    :param llm: AzureChatOpenAI model
    :param system_prompt_file_location: a text file containing the system prompt
    :param user_contract_description: description of the contract that user desires to map
    :return: string response
    """
    # get the AI prompt from the chosen text file containing prompt
    system_prompt_string = file_to_string_processor(system_prompt_file_location)
    system_prompt_string += "\nRespond ONLY with the exact category name, no additional text."
    prompt = [SystemMessage(content=system_prompt_string) , HumanMessage(content=user_contract_description.strip())]
    response = llm.invoke(prompt)
    return response.content


