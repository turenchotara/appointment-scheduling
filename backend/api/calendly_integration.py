import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, Query

from backend.models.schema import (
    AppointmentRequest,
    AppointmentResponse,
    AvailabilityResponse,
    SlotModel,
)
from . import calendly_router

# ---- Type Aliases ---- #
WorkingHours = dict[str, str]  # {"start": "09:00", "end": "17:00"}
AppointmentRecord = dict[str, Any]
DoctorSchedule = dict[str, Any]

# ---- Appointment durations (minutes) ---- #
APPOINTMENT_DURATIONS: dict[str, int] = {
    "General Consultation": 30,
    "Follow-up": 15,
    "Physical Exam": 45,
    "Specialist Consultation": 60,
}

# ---- Doctor's Schedule LOADED FROM JSON ---- #
SCHEDULE_FILE: str = os.path.join(os.path.dirname(__file__), '..', 'doctor_schedule.json')
with open(SCHEDULE_FILE, encoding="utf-8") as f:
    doctor_schedule: DoctorSchedule = json.load(f)


# ---- Utilities ---- #
def get_weekday_from_date(date_str: str) -> str:
    """Convert a date string to a weekday abbreviation.
    
    Args:
        date_str: Date in YYYY-MM-DD format.
        
    Returns:
        Weekday abbreviation (mon, tue, wed, thu, fri, sat, sun).
    """
    dt: datetime = datetime.strptime(date_str, "%Y-%m-%d")
    weekdays: list[str] = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    return weekdays[dt.weekday()]


def parse_time(t_str: str) -> datetime:
    """Parse a time string into a datetime object.
    
    Args:
        t_str: Time in HH:MM format.
        
    Returns:
        datetime object representing the time.
    """
    return datetime.strptime(t_str, "%H:%M")


def format_time(dt: datetime) -> str:
    """Format a datetime object as a time string.
    
    Args:
        dt: datetime object.
        
    Returns:
        Time string in HH:MM format.
    """
    return dt.strftime("%H:%M")


# ---- 1. AVAILABILITY ---- #
@calendly_router.get("/availability", response_model=AvailabilityResponse)
async def get_availability(
    date: str = Query(..., regex=r"^\d{4}-\d{2}-\d{2}$"),
    appointment_type: str = Query(...)
) -> AvailabilityResponse:
    """Get available appointment slots for a specific date and type.
    
    Args:
        date: The date to check availability for (YYYY-MM-DD format).
        appointment_type: The type of appointment to book.
        
    Returns:
        AvailabilityResponse with available time slots.
        
    Raises:
        HTTPException: If appointment type is invalid.
    """
    # Validate appointment_type
    if appointment_type not in APPOINTMENT_DURATIONS:
        raise HTTPException(status_code=400, detail="Invalid appointment type.")
    
    # Validate working weekday
    weekday: str = get_weekday_from_date(date)
    wh: WorkingHours | None = doctor_schedule["working_hours"].get(weekday)
    if not wh:
        return AvailabilityResponse(date=date, available_slots=[])

    required_minutes: int = APPOINTMENT_DURATIONS[appointment_type]
    start: datetime = parse_time(wh["start"])
    end: datetime = parse_time(wh["end"])
    
    # Build blocked intervals from booked appointments
    blocked: list[tuple[datetime, datetime]] = []
    for appt in doctor_schedule["existing_appointments"]:
        if appt["date"] == date:
            st: datetime = parse_time(appt["start_time"])
            et: datetime = st + timedelta(minutes=appt["duration"])
            blocked.append((st, et))
    
    # Generate candidate slots
    slots: list[SlotModel] = []
    current: datetime = start
    while current + timedelta(minutes=required_minutes) <= end:
        c_end: datetime = current + timedelta(minutes=required_minutes)
        overlap: bool = any(
            current < b_end and c_end > b_start 
            for b_start, b_end in blocked
        )
        if not overlap:
            slots.append(SlotModel(
                start_time=format_time(current),
                end_time=format_time(c_end),
                available=True
            ))
        current += timedelta(minutes=15)  # step granularity
    
    return AvailabilityResponse(date=date, available_slots=slots)


# ---- 2. BOOK APPOINTMENT ---- #
@calendly_router.post("/book", response_model=AppointmentResponse)
async def book_appointment(data: AppointmentRequest) -> AppointmentResponse:
    """Book a new appointment.
    
    Args:
        data: The appointment booking request data.
        
    Returns:
        AppointmentResponse with booking confirmation.
        
    Raises:
        HTTPException: If validation fails or slot is unavailable.
    """
    # Check for valid duration and slot
    required_minutes: int | None = APPOINTMENT_DURATIONS.get(data.appointment_type)
    if not required_minutes:
        raise HTTPException(status_code=400, detail="Invalid appointment type.")
    
    # Find working hours
    weekday: str = get_weekday_from_date(data.date)
    wh: WorkingHours | None = doctor_schedule["working_hours"].get(weekday)
    if not wh:
        raise HTTPException(status_code=400, detail="Doctor not available on this day.")
    
    slot_start: datetime = parse_time(data.start_time)
    slot_end: datetime = slot_start + timedelta(minutes=required_minutes)
    wh_start: datetime = parse_time(wh["start"])
    wh_end: datetime = parse_time(wh["end"])
    
    # Out of working hours?
    if slot_start < wh_start or slot_end > wh_end:
        raise HTTPException(
            status_code=400, 
            detail="Requested slot is outside of working hours."
        )
    
    # Conflicts?
    for appt in doctor_schedule["existing_appointments"]:
        if appt["date"] == data.date:
            appt_start: datetime = parse_time(appt["start_time"])
            appt_end: datetime = appt_start + timedelta(minutes=appt["duration"])
            if slot_start < appt_end and slot_end > appt_start:
                raise HTTPException(
                    status_code=409, 
                    detail="Requested slot overlaps with an existing appointment."
                )
    
    # Mock booking save
    booking_id: str = f"APPT-{str(uuid.uuid4())[:8]}"
    confirmation_code: str = uuid.uuid4().hex[:6].upper()
    
    new_appt: AppointmentRecord = {
        "date": data.date,
        "start_time": data.start_time,
        "appointment_type": data.appointment_type,
        "duration": required_minutes,
        "patient": data.patient.model_dump(),
        "reason": data.reason
    }
    doctor_schedule["existing_appointments"].append(new_appt)
    
    details: dict[str, str] = {
        "patient_name": data.patient.name,
        "appointment_type": data.appointment_type,
        "date": data.date,
        "start_time": data.start_time
    }
    
    return AppointmentResponse(
        booking_id=booking_id,
        status="confirmed",
        confirmation_code=confirmation_code,
        details=details
    )
