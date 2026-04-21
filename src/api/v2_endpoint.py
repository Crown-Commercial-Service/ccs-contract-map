import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel

# Redis & Identity Imports
from redis.asyncio import Redis
from azure.identity import DefaultAzureCredential
from redis_entraid.cred_provider import create_from_default_azure_credential

# Cache Imports
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.backends.inmemory import InMemoryBackend  # Added for fallback
from fastapi_cache.decorator import cache

from src.core.classification_v2 import contract_mapper_v2


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    REDIS_SCOPE = ("https://redis.azure.com/.default",)
    redis_host = os.getenv("REDIS_HOST")

    if redis_host:
        try:
            # Identity-based credential (works locally and in Azure) to run locally you need to set redis private endpoint config allow public network access
            cred_provider = create_from_default_azure_credential(scopes=REDIS_SCOPE)

            redis_client = Redis(
                host=redis_host,
                port=6380,
                ssl=True,
                credential_provider=cred_provider,# Mandatory for Entra ID: connection must be established to verify token
                socket_timeout=5
            )

            # Test connection immediately to ensure Entra ID/Network is valid
            await redis_client.ping()

            FastAPICache.init(RedisBackend(redis_client), prefix="ccs-mapper-cache")#the prefix creates a folder to store the specific cache
            print(f"✅ Redis Cache initialized")
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}. Falling back to InMemory cache.")
            FastAPICache.init(InMemoryBackend(), prefix="ccs-mapper-cache")
    else:
        # No REDIS_HOST provided: Resort to local memory caching
        print("ℹ️ REDIS_HOST not found. Using local InMemory cache (No persistence).")
        FastAPICache.init(InMemoryBackend(), prefix="ccs-mapper-cache")

    yield
    # --- Shutdown ---


app = FastAPI(lifespan=lifespan)


class ContractDescription(BaseModel):
    description: str


@app.post("/map")
@cache(expire=3600)
async def run_contract_mapper(body: ContractDescription):
    try:
        response = await contract_mapper_v2(user_contract_description=body.description)
        print(response)
        return {"AI_label": response}
    except Exception as e:
        print("Error:", e)
        return {"error": str(e)}
