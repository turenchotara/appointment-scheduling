from typing import List, Dict, Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_query: str
    session_id: str


# Calendly Models
class PatientModel(BaseModel):
    name: str
    email: str
    phone: str


class AppointmentRequest(BaseModel):
    appointment_type: str = Field(...)
    date: str = Field(...)
    start_time: str = Field(...)
    patient: PatientModel
    reason: str


class AppointmentResponse(BaseModel):
    booking_id: str
    status: str
    confirmation_code: str
    details: Dict[str, Any]


class SlotModel(BaseModel):
    start_time: str
    end_time: str
    available: bool


class AvailabilityResponse(BaseModel):
    date: str
    available_slots: List[SlotModel]
