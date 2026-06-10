import json
from pathlib import Path
import requests

def clean_fastapi_openapi_json(raw_json):
    try:
        spec = raw_json

        # 1. Downgrade version
        spec["openapi"] = "3.0.1"

        # 2. Fix 'anyOf' in Validation Errors
        if "components" in spec and "schemas" in spec["components"]:
            ve = spec["components"]["schemas"].get("ValidationError")
            if isinstance(ve, dict) and "properties" in ve:
                loc = ve["properties"].get("loc", {})
                if "items" in loc:
                    loc["items"] = {"type": "string"}

        # 3. Handle Paths and Operations
        if "paths" in spec:
            for path_item in spec["paths"].values():
                if not isinstance(path_item, dict):
                    continue

                for operation in path_item.values():
                    if not isinstance(operation, dict):
                        continue

                    # ADDED: Fix 'examples' (plural) to 'example' (singular) for APIM 3.0.1
                    # APIM 3.0.1 will fail if it sees the 3.1.0 'examples' array
                    parameters = operation.get("parameters", [])
                    for param in parameters:
                        if "examples" in param:
                            # Just take the first example and make it the 'example'
                            first_ex = list(param["examples"].values())[0] if isinstance(param["examples"],
                                                                                         dict) else ""
                            param["example"] = first_ex
                            del param["examples"]

                    # Existing Response cleaning
                    responses = operation.get("responses", {})
                    for res in responses.values():
                        content = res.get("content", {})
                        for media_type in content.values():
                            if "schema" in media_type and not media_type["schema"]:
                                media_type["schema"] = {"type": "object"}

                            # ADDED: Recursive anyOf cleanup for complex Pydantic models
                            # This ensures fields like 'string | null' don't break the import
                            schema = media_type.get("schema", {})
                            if "anyOf" in schema:
                                # Simple fix: just use the first type in the list
                                first_type = schema["anyOf"][0]
                                media_type["schema"] = first_type

        return json.dumps(spec, indent=4)

    except json.JSONDecodeError:
        print("Error: Input is not valid JSON. Backend might have sent an HTML error page.")
        return raw_json
    except Exception as e:
        print(f"Cleaning failed: {e}")
        return raw_json

def create_fastapi_openapi_json(fastapi_openapi_json, target_dir=None):

    if target_dir:
        output_dir = Path(target_dir)
    else:
        output_dir = Path.cwd() / 'output'

    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / 'openapi.json'

    try:
        clean_data = clean_fastapi_openapi_json(fastapi_openapi_json)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(clean_data)
        return (True, file_path, clean_data)
    except requests.exceptions.RequestException as e:
        return (False, e)