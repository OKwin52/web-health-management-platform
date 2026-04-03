from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EncounterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    external_id: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    encounter_class: str | None = None
    code: str | None = None
    description: str | None = None
    reason_code: str | None = None
    reason_description: str | None = None
    created_at: datetime
    updated_at: datetime


class ConditionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    encounter_id: int | None = None
    source_key: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    code: str | None = None
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class MedicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    encounter_id: int | None = None
    source_key: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    code: str | None = None
    description: str | None = None
    reason_code: str | None = None
    reason_description: str | None = None
    base_cost: float | None = None
    payer_coverage: float | None = None
    dispenses: int | None = None
    total_cost: float | None = None
    created_at: datetime
    updated_at: datetime


class ObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    encounter_id: int | None = None
    source_key: str
    observed_at: datetime | None = None
    category: str | None = None
    code: str | None = None
    description: str | None = None
    value_text: str | None = None
    units: str | None = None
    value_type: str | None = None
    created_at: datetime
    updated_at: datetime
