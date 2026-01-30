import httpx
from utils import logger
from app import contract_mapper
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path


app = FastAPI()

class ContractDescription(BaseModel):
    description: str

system_prompt_file_location = Path.cwd() / "new_system_prompt.txt"

@app.post("/map")
async def run_contract_mapper(body: ContractDescription):
    async with httpx.AsyncClient() as client:
        try:
            response = await contract_mapper(user_contract_description=body.description, system_prompt_file_location=system_prompt_file_location)
            logger.info(response)
            return {"AI_label": response.content}
        except Exception as e:
            logger.exception("Error:", e)
            return {"error": str(e)}
