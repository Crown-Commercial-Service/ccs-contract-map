from contract_mapping_v2 import contract_mapper_v2
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
import git


app = FastAPI()

class ContractDescription(BaseModel):
    description: str



@app.post("/map")
def run_contract_mapper(body: ContractDescription):
    try:
        response = contract_mapper_v2(user_contract_description=body.description)
        print(response)
        return {"AI_label": response}
    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}


@app.get("/model_info")
def model_info():
    """
    Provides metadata about the currently deployed model.
    """
    try:
        # Robustly define the files that constitute the model
        model_files = [
            Path.cwd() / "python_system_prompt.py",
            Path.cwd() / "contract_mapping_v2.py"
        ]

        # Find the most recent modification time among the model files
        latest_update = max(
            datetime.fromtimestamp(p.stat().st_mtime) for p in model_files if p.exists()
        )

        # Retrieve a git commit hash for cases where files were updated multiple times on the same day
        repo = git.Repo(search_parent_directories=True)
        commit_hash = repo.head.object.hexsha

        return {
            "last_updated": latest_update,
            "version": commit_hash
        }
    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}


