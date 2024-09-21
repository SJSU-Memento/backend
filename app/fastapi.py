from fastapi import FastAPI, APIRouter
from app.routes import memory


app = FastAPI(title="Memento API", version="0.1.0")

api = APIRouter(prefix="/api")
api.include_router(memory.router)

app.include_router(api)
