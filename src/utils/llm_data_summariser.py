from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
from pathlib import Path
import os


load_dotenv()
llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
        azure_deployment=os.getenv("DEPLOYMENT_NAME"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature=0.0
    )



system_prompt_file = (
    Path(__file__).parent.parent.parent / "prompts/summariser_system_prompt.md"
)


def get_system_prompt():
    with open(system_prompt_file, "r", encoding="utf-8") as f:
        return f.read()


def summarise_llm(text):
    system_content = get_system_prompt()

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=f"Please summarize the following text:\n\n{text}")
    ]

    response = llm.invoke(messages)
    return response.content