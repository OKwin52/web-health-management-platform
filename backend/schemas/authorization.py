from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.models.authorization import AuthorizationStatus


class AuthorizationCreate(BaseModel):
    patient_id: int
    doctor_id: int


class AuthorizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    doctor_id: int
    status: AuthorizationStatus
    granted_at: datetime
    revoked_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
