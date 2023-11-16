from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import httpx
import asyncio
from typing import Optional
from consts import GIS_DOMAIN, ORIGINS
app = FastAPI()

class Settings(BaseModel):
    max_requests: int = 1000

settings = Settings()

class User:
    def __init__(self, request_count: int = 0):
        self.request_count = request_count

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_user(db: User = Depends(User)) -> User:
    return db

semaphore = asyncio.Semaphore(30)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/settings")
async def update_settings(new_settings: Settings):
    global settings
    settings = new_settings
    return {"message": "Settings updated"}

@app.get("/{service_path:path}/tile/{z}/{x}/{y}")
async def handle_tile(service_path: str, z: int, x: int, y: int, user: User = Depends(get_user)):
    if user.request_count >= settings.max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"},
        )
    
    user.request_count += 1

    async with semaphore:
        redirect_url = f"{GIS_DOMAIN}/{service_path}/tile/{z}/{x}/{y}?blankTile=false"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(redirect_url)
            response.raise_for_status() 
            binary_data: bytes = response.content

        return Response(content=binary_data, media_type="image/png")

@app.get("/{service_path:path}")
async def handle_request(service_path: str):
    redirect_url = f"{GIS_DOMAIN}/{service_path}?f=json"

    async with httpx.AsyncClient() as client:
        response = await client.get(redirect_url)
        response.raise_for_status()

        return JSONResponse(content=response.json(), status_code=response.status_code)
