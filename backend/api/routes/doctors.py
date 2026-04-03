from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.api.deps import get_current_user
from backend.db import get_db
from backend.models import Doctor, User
from backend.schemas.doctor import DoctorResponse


router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("", response_model=list[DoctorResponse])
def list_doctors(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Doctor]:
    return db.scalars(select(Doctor).options(joinedload(Doctor.user)).order_by(Doctor.id)).unique().all()
