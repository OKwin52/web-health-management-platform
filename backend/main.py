from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.api.router import api_router
from backend.core.config import settings


app = FastAPI(title=settings.app_name)
app.include_router(api_router)
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


@app.get("/", include_in_schema=False)
def index() -> RedirectResponse:
    return RedirectResponse(url="/frontend/index.html")
