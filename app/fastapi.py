from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles

from app.routes import memory
from app.routes import upload


app = FastAPI(title="Memento API", version="0.1.0")

api = APIRouter(prefix="/api")
api.include_router(upload.router)
api.include_router(memory.router)

app.include_router(api)