from contract_mapping_v2 import contract_mapper_v2
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from pathlib import Path
import os
import secrets
from passlib.context import CryptContext

app = FastAPI()

security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class ContractDescription(BaseModel):
    description: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    stored_hashed_password = os.getenv("HASHED_PASSWORD")
    if not stored_hashed_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error: Hashed password not configured.",
        )

    is_correct_password = verify_password(credentials.password, stored_hashed_password)
    
    # Use secrets.compare_digest for a constant-time comparison to help prevent timing attacks
    # This is a bit redundant with modern password hashing libraries but adds an extra layer of security.
    # A simple boolean check `if is_correct_password:` is generally sufficient with passlib.
    # However, to be explicit about timing attack resistance:
    if not secrets.compare_digest(str(is_correct_password).encode("utf-8"), "True".encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.post("/map")
def run_contract_mapper(body: ContractDescription, username: str = Depends(get_current_user)):
    try:
        response = contract_mapper_v2(user_contract_description=body.description)
        print(response)
        return {"AI_label": response}
    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}

