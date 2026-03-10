from contract_mapping_v2 import contract_mapper_v2
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
from utils import logger


app = FastAPI()

class ContractDescription(BaseModel):
    description: str



@app.post("/map")
async def run_contract_mapper(body: ContractDescription):
    try:
        response = await contract_mapper_v2(user_contract_description=body.description)
        print(response)
        logger.info(response)
        return {"AI_label": response}
    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}
