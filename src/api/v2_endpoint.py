from src.core.classification_v2 import contract_mapper_v2
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel


app = FastAPI()


class ContractDescription(BaseModel):
    description: str


@app.post("/map")
async def run_contract_mapper(body: ContractDescription):
    try:
        response = await contract_mapper_v2(user_contract_description=body.description)
        print(response)
        return {"AI_label": response}
    except Exception as e:
        print(f"Internal Server Error: {e}")

        # Raise an HTTPException so FastAPI returns a 500 status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the contract mapping."
        )
