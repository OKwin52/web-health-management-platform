from fastapi import APIRouter

from backend.api.routes.archive import router as archive_router
from backend.api.routes.authorizations import router as authorizations_router
from backend.api.routes.auth import router as auth_router
from backend.api.routes.doctors import router as doctors_router
from backend.api.routes.health import router as health_router
from backend.api.routes.patients import router as patients_router


api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(doctors_router)
api_router.include_router(patients_router)
api_router.include_router(archive_router)
api_router.include_router(authorizations_router)
