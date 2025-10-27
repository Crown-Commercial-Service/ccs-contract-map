from contract_mapping_v2 import contract_mapper_v2
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime


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

@app.post("/model_version")
def metadata():
    system_prompt_file = Path.cwd() / "python_system_prompt.py"
    llm_script_file = Path.cwd() / "contract_mapping_v2.py"
    try:
        system_prompt_file_stat = system_prompt_file.stat()
        llm_script_file_stat = llm_script_file.stat()
        system_prompt_file_modified_time = datetime.fromtimestamp(system_prompt_file_stat.st_mtime)
        llm_script_file_modified_time = datetime.fromtimestamp(llm_script_file_stat.st_mtime)
        with open(Path.cwd() / "contract_map_update_logs.txt", "r") as f:
            last_update = f.readlines()
        if len(last_update) == 0:
            with open(Path.cwd() / "contract_map_update_logs.txt", "w") as f:
                latest_date = max(system_prompt_file_modified_time, llm_script_file_modified_time)
                f.write(str(latest_date))
                return {"models_latest_update":latest_date}
        if len(last_update) == 1:
            lastest_date = max(system_prompt_file_modified_time, llm_script_file_modified_time)

            if lastest_date > datetime.strptime(last_update[0].strip(), "%Y-%m-%d %H:%M:%S.%f" ):
                with open(Path.cwd() / "contract_map_update_logs.txt", "w") as f:
                    f.write(str(lastest_date))
                    return {"models_latest_update": lastest_date}
            else:
                return {"models_latest_update": last_update[0]}

    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}

