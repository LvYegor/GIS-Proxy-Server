from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx
from celery import Celery
from celery.result import AsyncResult
from consts import GIS_DOMAIN, ORIGINS

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

celery = Celery(
    "tasks", 
    broker="redis://localhost:6379", 
    backend="redis://localhost:6379"
)

@celery.task
def fetch_tile(redirect_url):
    with httpx.Client() as client:
        response = client.get(redirect_url)
        response.raise_for_status()
        return response.content

@app.get("/{service_path:path}/tile/{z}/{x}/{y}")
async def handle_tile(service_path: str, z: int, x: int, y: int):
    redirect_url = f"{GIS_DOMAIN}/{service_path}/tile/{z}/{x}/{y}?blankTile=false"
    result = fetch_tile.delay(redirect_url)
    fin_result = AsyncResult(result.id)

    return Response(content=fin_result.get(), media_type="image/png")

    

@app.get("/{service_path:path}")
async def handle_request(service_path: str):
    # URL of destination server
    redirect_url = f"{GIS_DOMAIN}/{service_path}?f=json"    

    # Request to destination server
    async with httpx.AsyncClient() as client:
        response = await client.get(redirect_url)

        # Check the success of the request to the destination server
        response.raise_for_status()

        return JSONResponse(content=response.json(), status_code=response.status_code)