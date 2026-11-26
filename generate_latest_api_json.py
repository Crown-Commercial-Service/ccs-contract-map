from src.api.v3_endpoint import app
from src.utils.api_to_openapi_json import create_fastapi_openapi_json

openapi_json = app.openapi()

def get_openapi_json():
    return create_fastapi_openapi_json(openapi_json)

get_openapi_json()
