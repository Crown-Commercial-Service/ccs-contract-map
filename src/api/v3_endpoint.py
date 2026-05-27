from src.core.classification_v2_mix_v5 import keywords_and_llm
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()


class ContractDescription(BaseModel):
    description: str


@app.post("/map")
async def run_contract_mapper(body: ContractDescription):
    try:
        response, _, _ = await keywords_and_llm(
            description=body.description, threshold=3, margin=5
        )
        print(response)
        return {"AI_label": response}
    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}
