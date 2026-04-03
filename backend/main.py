from fastapi import FastAPI

from backend.api.router import api_router
from backend.core.config import settings


app = FastAPI(title=settings.app_name)
app.include_router(api_router)
