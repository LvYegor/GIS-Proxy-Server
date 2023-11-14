from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx
import io
from consts import GIS_DOMAIN

BASE_URL = "https://gismap.by/server1/rest/services"

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Замените это на адрес вашего клиента
    allow_credentials=True,
    allow_methods=["*"],  # или указать методы, которые разрешены
    allow_headers=["*"],  # или указать заголовки, которые разрешены
    
)


@app.get("/server1/rest/services/{service_path:path}")
async def handle_request(service_path: str):
    # Сформируйте URL для перенаправления
    redirect_url = f"{BASE_URL}/{service_path}?f=json"    

    # Выполните запрос к конечному сервису
    async with httpx.AsyncClient() as client:
        response = await client.get(redirect_url)

        # Проверьте успешность запроса к конечному сервису
        response.raise_for_status()

        # Верните ответ от конечного сервиса
        return JSONResponse(content=response.json(), status_code=response.status_code)



@app.get("/server1/rest/services/{service_path}/tile/{z}/{x}/{y}")
async def handle_tile(service_path: str, z: int, x: int, y: int):
    # Сформируйте URL для перенаправления
    redirect_url = f"{BASE_URL}/{service_path}/tile/{z}/{x}/{y}?blankTile=false"

    print("\n\n" + redirect_url + "\n\n")

    # Выполните запрос к конечному сервису
    async with httpx.AsyncClient() as client:
        response = await client.get(redirect_url)

        # Проверьте успешность запроса к конечному сервису
        response.raise_for_status()

        binary_data: bytes = response.content

        # Верните ответ от конечного сервиса
        return Response(content=binary_data, media_type="image/png")
