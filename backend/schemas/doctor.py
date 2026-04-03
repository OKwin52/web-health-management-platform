from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.schemas.user import UserSummary


class DoctorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    full_name: str
    department: str | None = None
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    user: UserSummary
