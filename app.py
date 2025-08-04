# from importlib.metadata import pass_none
from langchain_openai import AzureChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os
from file_engineering.file_to_string import file_to_string_processor


load_dotenv()

# system_prompt_file_location = Path.cwd() / "contractmap_prompt_with_descriptions.txt"
#
# system_prompt_string = file_to_string_processor(system_prompt_file_location)
#
#
# prompt = ChatPromptTemplate.from_messages([SystemMessagePromptTemplate.from_template(system_prompt_string + "{input}")])
#


llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_deployment=os.getenv("DEPLOYMENT_NAME"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0.0,
    top_p=1,
)


# chain = prompt | llm
# response = chain.invoke({ "input":"This Contract Award Notice covers electricity and/or gas supply procurement services awarded via the Dynamic Purchasing System (DPS). The DPS is available for use by all contracting authorities within England, Scotland, Wales and Northern Ireland as defined by Regulation 2 of the Public Contracts Regulations 2015 #102. The tender process was managed by Equity Energies."})
# new_prompt = [SystemMessage(content=system_prompt_string) , HumanMessage(content="CCTV SAFER STREETS INITIATIVE CCTV 15 CAMERAS 5 SPOT CAMERAS WIRELESS LINK TO CONTROL ROOM CONNECTIONS AND EQUIPMENT")]
# response2 = llm(new_prompt)
# # print(response.content)
# print(response2.content)

#creating function of code
#SystemMessage(content="Respond ONLY with the exact category name, no additional text.")

def contract_mapper(system_prompt_file_location, user_contract_description, llm=llm):
    """

    :param llm: AzureChatOpenAI model
    :param system_prompt_file_location: a text file containing the system prompt
    :param user_contract_description: description of the contract that user desires to map
    :return: string response
    """
    # get the AI prompt from the chosen text file containing prompt
    system_prompt_string = file_to_string_processor(system_prompt_file_location)
    system_prompt_string += "\nRespond ONLY with the exact category name, no additional text."
    prompt = [SystemMessage(content=system_prompt_string) , HumanMessage(content=user_contract_description.strip())]
    response = llm.predict_messages(prompt)
    return response.content


    # # setup system prompt for AI
    # prompt = ChatPromptTemplate.from_messages(
    #     [SystemMessagePromptTemplate.from_template(system_prompt_string + "{input}")])
    # chain = prompt | llm
    # response = chain.invoke({"input":user_contract_description})
    # return response.content
