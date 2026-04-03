from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from backend.schemas.user import UserSummary


class PatientBase(BaseModel):
    full_name: str
    date_of_birth: date | None = None
    gender: str | None = None
    phone: str | None = None
    address: str | None = None


class PatientCreate(PatientBase):
    username: str
    password: str


class PatientUpdate(BaseModel):
    full_name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    phone: str | None = None
    address: str | None = None


class PatientResponse(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    user: UserSummary
