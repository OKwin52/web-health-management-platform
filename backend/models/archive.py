from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class Encounter(TimestampMixin, Base):
    __tablename__ = "encounters"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    encounter_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reason_description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    patient = relationship("Patient", back_populates="encounters")
    conditions = relationship("Condition", back_populates="encounter")
    medications = relationship("Medication", back_populates="encounter")
    observations = relationship("Observation", back_populates="encounter")


class Condition(TimestampMixin, Base):
    __tablename__ = "conditions"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    encounter_id: Mapped[int | None] = mapped_column(ForeignKey("encounters.id"), nullable=True, index=True)
    source_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    patient = relationship("Patient", back_populates="conditions")
    encounter = relationship("Encounter", back_populates="conditions")


class Medication(TimestampMixin, Base):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    encounter_id: Mapped[int | None] = mapped_column(ForeignKey("encounters.id"), nullable=True, index=True)
    source_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reason_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    base_cost: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    payer_coverage: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    dispenses: Mapped[int | None] = mapped_column(nullable=True)
    total_cost: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    patient = relationship("Patient", back_populates="medications")
    encounter = relationship("Encounter", back_populates="medications")


class Observation(TimestampMixin, Base):
    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    encounter_id: Mapped[int | None] = mapped_column(ForeignKey("encounters.id"), nullable=True, index=True)
    source_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    units: Mapped[str | None] = mapped_column(String(50), nullable=True)
    value_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    patient = relationship("Patient", back_populates="observations")
    encounter = relationship("Encounter", back_populates="observations")
