from src.core.classification_v2 import contract_mapper_v2
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()


class ContractDescription(BaseModel):
    description: str


@app.post("/v1/map")
async def run_contract_mapper(body: ContractDescription):
    try:
        response = await contract_mapper_v2(user_contract_description=body.description)
        print(response)
        return {"AI_label": response}
    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}
