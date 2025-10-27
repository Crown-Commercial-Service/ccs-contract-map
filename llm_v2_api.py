from contract_mapping_v2 import contract_mapper_v2
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import os


app = FastAPI()

class ContractDescription(BaseModel):
    description: str

class Password(BaseModel):
    password: str



@app.post("/map")
def run_contract_mapper(body: ContractDescription, password: Password):
    try:
        if password.password == os.getenv("password"):
            response = contract_mapper_v2(user_contract_description=body.description)
            print(response)
            return {"AI_label": response}
        else:
            return {"error": "Password does not match"}
    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}
