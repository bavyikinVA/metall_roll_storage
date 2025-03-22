from fastapi import FastAPI
from src.api import main_router
from src.config import settings
import uvicorn

app = FastAPI()
app.include_router(main_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)