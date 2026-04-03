from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class AuthorizationStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"


class PatientDoctorAuthorization(TimestampMixin, Base):
    __tablename__ = "patient_doctor_authorizations"
    __table_args__ = (UniqueConstraint("patient_id", "doctor_id", name="uq_patient_doctor_pair"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    status: Mapped[AuthorizationStatus] = mapped_column(
        SqlEnum(AuthorizationStatus), default=AuthorizationStatus.ACTIVE, nullable=False
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    patient = relationship("Patient", back_populates="authorizations")
    doctor = relationship("Doctor", back_populates="authorizations")
