from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from openai import AsyncAzureOpenAI
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelSettings
from dotenv import load_dotenv
from pathlib import Path
from typing import List
import os

load_dotenv()

DEFAULT_SYSTEM_PROMPT_FILE = (
    Path(__file__).parent.parent.parent / "prompts/keyword_system_prompt_v2.md"
)


class KeywordsFinder(BaseModel):
    primary: List[str] = Field(
        description="High-precision nouns exclusive to this category (e.g., 'kerosene'). Max 15 words.",
        min_length=1,
    )
    secondary: List[str] = Field(
        description="Supporting context words often found in this category (e.g., 'supply'). Max 20 words.",
        min_length=1,
    )


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


def keywords_finder_llm(description):
    llm = Agent(
        model=model,
        output_type=KeywordsFinder,
        model_settings=ModelSettings(
            temperature=0.0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            seed=42,
        ),
    )

    with open(DEFAULT_SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
        raw_prompt_template = f.read()

    prompt = raw_prompt_template.replace("{{combined_text}}", description)

    result = llm.run_sync(prompt)
    return result.output.primary, result.output.secondary
