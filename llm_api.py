from app import contract_mapper
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path


app = FastAPI()

class ContractDescription(BaseModel):
    description: str

system_prompt_file_location = Path.cwd() / "new_system_prompt.txt"

@app.post("/map")
def run_contract_mapper(body: ContractDescription):
    try:
        response = contract_mapper(user_contract_description=body.description, system_prompt_file_location=system_prompt_file_location)
        print(response)
        return {"AI_label": response}
    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}
