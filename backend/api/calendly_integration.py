import json
import os
import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException, Query

from backend.models.schema import AppointmentRequest, AppointmentResponse, AvailabilityResponse
from ..api import calendly_router

# ---- Appointment durations (minutes) ---- #
APPOINTMENT_DURATIONS = {
    "General Consultation": 30,
    "Follow-up": 15,
    "Physical Exam": 45,
    "Specialist Consultation": 60,
}

# ---- Doctor's Schedule LOADED FROM JSON ---- #
SCHEDULE_FILE = os.path.join(os.path.dirname(__file__), '..', 'doctor_schedule.json')
with open(SCHEDULE_FILE, encoding="utf-8") as f:
    doctor_schedule = json.load(f)


# ---- Utilities ---- #
def get_weekday_from_date(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][dt.weekday()]


def parse_time(t_str: str) -> datetime:
    return datetime.strptime(t_str, "%H:%M")


def format_time(dt: datetime) -> str:
    return dt.strftime("%H:%M")


# ---- 1. AVAILABILITY ---- #
@calendly_router.get("/availability", response_model=AvailabilityResponse)
async def get_availability(date: str = Query(..., regex=r"^\\d{4}-\\d{2}-\\d{2}$"), appointment_type: str = Query(...)):
    # Validate appointment_type
    if appointment_type not in APPOINTMENT_DURATIONS:
        raise HTTPException(status_code=400, detail="Invalid appointment type.")
    # Validate working weekday
    weekday = get_weekday_from_date(date)
    wh = doctor_schedule["working_hours"].get(weekday)
    if not wh:
        return {"date": date, "available_slots": []}

    required_minutes = APPOINTMENT_DURATIONS[appointment_type]
    start = parse_time(wh["start"])
    end = parse_time(wh["end"])
    # Build blocked intervals from booked appointments
    blocked = []
    for appt in doctor_schedule["existing_appointments"]:
        if appt["date"] == date:
            st = parse_time(appt["start_time"])
            et = st + timedelta(minutes=appt["duration"])
            blocked.append((st, et))
    # Generate candidate slots
    slots = []
    current = start
    while current + timedelta(minutes=required_minutes) <= end:
        c_end = current + timedelta(minutes=required_minutes)
        overlap = any(current < b_end and c_end > b_start for b_start, b_end in blocked)
        if not overlap:
            slots.append({
                "start_time": format_time(current),
                "end_time": format_time(c_end),
                "available": True
            })
        current += timedelta(minutes=15)  # step granularity
    return {"date": date, "available_slots": slots}


# ---- 2. BOOK APPOINTMENT ---- #
@calendly_router.post("/book", response_model=AppointmentResponse)
async def book_appointment(data: AppointmentRequest):
    # Check for valid duration and slot
    required_minutes = APPOINTMENT_DURATIONS.get(data.appointment_type)
    if not required_minutes:
        raise HTTPException(status_code=400, detail="Invalid appointment type.")
    # Find working hours
    weekday = get_weekday_from_date(data.date)
    wh = doctor_schedule["working_hours"].get(weekday)
    if not wh:
        raise HTTPException(status_code=400, detail="Doctor not available on this day.")
    slot_start = parse_time(data.start_time)
    slot_end = slot_start + timedelta(minutes=required_minutes)
    wh_start = parse_time(wh["start"])
    wh_end = parse_time(wh["end"])
    # Out of working hours?
    if slot_start < wh_start or slot_end > wh_end:
        raise HTTPException(status_code=400, detail="Requested slot is outside of working hours.")
    # Conflicts?
    for appt in doctor_schedule["existing_appointments"]:
        if appt["date"] == data.date:
            appt_start = parse_time(appt["start_time"])
            appt_end = appt_start + timedelta(minutes=appt["duration"])
            if slot_start < appt_end and slot_end > appt_start:
                raise HTTPException(status_code=409, detail="Requested slot overlaps with an existing appointment.")
    # Mock booking save:
    booking_id = f"APPT-{str(uuid.uuid4())[:8]}"
    confirmation_code = uuid.uuid4().hex[:6].upper()
    new_appt = {
        "date": data.date,
        "start_time": data.start_time,
        "appointment_type": data.appointment_type,
        "duration": required_minutes,
        "patient": data.patient.dict(),
        "reason": data.reason
    }
    doctor_schedule["existing_appointments"].append(new_appt)
    details = {
        "patient_name": data.patient.name,
        "appointment_type": data.appointment_type,
        "date": data.date,
        "start_time": data.start_time
    }
    return {
        "booking_id": booking_id,
        "status": "confirmed",
        "confirmation_code": confirmation_code,
        "details": details
    }
