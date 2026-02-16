import httpx
from typing import Dict, Any
from utils import logger
from contract_mapping_v2 import contract_mapper_v2
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
import uvicorn
from pydantic import BaseModel
from pathlib import Path


app = FastAPI()


class ContractDescription(BaseModel):
    description: str



@app.post("/map")
async def run_contract_mapper(body: ContractDescription):
    try:
        response = contract_mapper_v2(user_contract_description='test', system_prompt='')
        logger.info(response)
        return {"AI_label": response}
    except Exception as e:
        logger.exception("Error:", str(e))
        return {"error": str(e)}
