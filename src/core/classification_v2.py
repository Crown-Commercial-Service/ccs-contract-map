from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
import os
from pathlib import Path
from src.utils.file_to_string import file_to_string_processor
from functools import lru_cache

load_dotenv()


DEFAULT_SYSTEM_PROMPT_FILE = (
    Path(__file__).parent.parent.parent / "prompts/system_prompt_v2.md"
)


@lru_cache(maxsize=1)
def _build_llm():
    return AzureChatOpenAI(
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


def _resolve_system_prompt(system_prompt=None, system_prompt_file_location=None):
    if system_prompt is not None:
        return system_prompt

    prompt_file = system_prompt_file_location or DEFAULT_SYSTEM_PROMPT_FILE
    return file_to_string_processor(prompt_file)


async def contract_mapper_v2(
    user_contract_description,
    llm=None,
    system_prompt=None,
    system_prompt_file_location=None,
):
    llm = llm or _build_llm()
    resolved_system_prompt = _resolve_system_prompt(
        system_prompt=system_prompt,
        system_prompt_file_location=system_prompt_file_location,
    )

    input_prompt = f"\n user input:{user_contract_description} "
    response = llm.invoke(resolved_system_prompt + input_prompt)

    return response.content
