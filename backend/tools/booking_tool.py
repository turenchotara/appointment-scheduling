from datetime import datetime
from typing import Any, List

import aiohttp
import pytz
from langchain.tools import tool
from pydantic import BaseModel, Field

from backend import settings, logger


class FieldBooking(BaseModel):
    __repr_name__ = "booking fields"

    name: str = Field(..., description="Name of the booking")
    email: str = Field(..., description="Email of the booking (e.g user@gmail.com)",
                       pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    phoneNumber: str = Field(..., description="Phone number of the booking (e.g +91 9896121856)",
                             pattern=r"^\+91[- ]?[6-9]\d{   9}$")
    notes: str = Field(description="Notes about the booking")
    rescheduleReason: str = Field(..., description="Reason why the booking is rejected")


class BookingData(BaseModel):
    session_type: str = Field(..., description="Type of the session which need to check for availability")
    session_date: str = Field(...,
                              description="Date of the session for which availability needs to be checked in YYYY-MM-DD format")
    booking_time: str = Field(..., description="Time of slot booking in HH:MM formate.")
    booking_fields: FieldBooking = Field(..., description="Booking information which are required for booking")


@tool(args_schema=BookingData)
async def book_appointment(session_type: str, session_date: str, booking_time: str, booking_fields: FieldBooking):
    """
    Tool to book appointments.
    :return:
    """
    url = "https://api.cal.com/v2/bookings"

    try:
        local_tz = pytz.timezone("Asia/Kolkata")
        # Parse the datetime string first
        dt = datetime.strptime(f"{session_date} {booking_time}", "%Y-%m-%d %H:%M")
        # Localize to the timezone
        date_time = local_tz.localize(dt)
        utc_dt = date_time.astimezone(pytz.utc)
        utc_dt = utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError as e:
        logger.error(f"Error parsing date/time: {e}")
        return f"Sorry, there was an error with the date or time format. Please ensure the date is in YYYY-MM-DD format and time is in HH:MM format."

    try:
        result = await get_event_type()
        if result:
            for e_type in result:
                if session_type == e_type["title"]:
                    session_type_id = e_type["id"]
                    break
                else:
                    session_type_id = ""

        else:
            raise ValueError("Due to some internal issue i can't book an appointment.")

        payload = {
            "eventTypeId": session_type_id,
            "start": utc_dt,
            "attendee": {
                "name": booking_fields.name,
                "email": booking_fields.email,
                "timeZone": "Asia/Kolkata",
                "phoneNumber": booking_fields.phoneNumber,
            },
            "bookingFieldsResponses": {
                "attendeePhoneNumber": booking_fields.phoneNumber,
                "rescheduleReason": booking_fields.rescheduleReason,
            }
        }

        notes = booking_fields.notes
        if notes:
            payload['bookingFieldsResponses']['notes'] = notes

        headers = {
            "Authorization": f"Bearer {settings.API_KEY}",
            "cal-api-version": "2024-08-13"
        }

        logger.info(f"Booking appointment for {booking_fields.name} on {session_date} at {booking_time}")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload,
                                    timeout=aiohttp.ClientTimeout(total=30)) as response:
                # Check HTTP status code
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    try:
                        error_data = await response.json()
                        error_message = error_data.get("message", error_data.get("error", "Unknown error"))
                    except:
                        error_message = error_text if error_text else "Unknown error"

                    if response.status == 401:
                        return "Sorry, I'm unable to book the appointment due to authentication issues. Please contact support."
                    elif response.status == 400:
                        return f"Sorry, I couldn't book the appointment. {error_message}. Please check your booking details and try again."
                    elif response.status == 404:
                        return f"Sorry, the session type '{session_type_id}' was not found. Please check the session type and try again."
                    elif response.status == 409:
                        return f"Sorry, the selected time slot is no longer available. {error_message}. Please choose a different time."
                    elif response.status == 429:
                        return "Sorry, too many requests. Please try again in a moment."
                    elif response.status >= 500:
                        return "Sorry, the booking service is currently unavailable. Please try again later."
                    else:
                        return f"Sorry, I encountered an error while booking the appointment (status {response.status}). {error_message}"

                # Parse JSON response
                try:
                    data = await response.json()
                    logger.info(f"Booking response: {data}")
                except Exception as json_error:
                    logger.error(f"Failed to parse JSON response: {json_error}")
                    return "Sorry, I received an invalid response from the booking service. Please try again."

                # Process successful response
                if response.status == 200 or response.status == 201:
                    booking_id = data.get("data", {}).get("id")
                    booking_uid = data.get("data", {}).get("uid")

                    if booking_id or booking_uid:
                        confirmation_msg = f"Appointment booked successfully!"
                        if booking_id:
                            confirmation_msg += f"\nBooking ID: {booking_id}"
                        if booking_uid:
                            confirmation_msg += f"\nConfirmation code: {booking_uid[:8]}"
                        confirmation_msg += f"\n\nDetails:\n- Date: {session_date}\n- Time: {booking_time}\n- Patient: {booking_fields.name}"
                        return confirmation_msg
                    else:
                        # Response is successful but doesn't have expected structure
                        return f"Appointment booking request processed. Please check your email for confirmation."
                else:
                    error_message = data.get("message", "Unknown error")
                    logger.warning(f"Unexpected response status {response.status}: {error_message}")
                    return f"Sorry, I received an unexpected response from the booking service. {error_message}"

    except aiohttp.ClientTimeout:
        logger.error("Request timeout while booking appointment")
        return "Sorry, the request timed out while booking the appointment. Please try again."
    except aiohttp.ClientResponseError as e:
        logger.error(f"Client response error: {e.status} - {e.message}")
        return f"Sorry, I encountered an error from the booking service (status {e.status}). Please try again."
    except aiohttp.ClientError as e:
        logger.error(f"Client error while booking appointment: {e}")
        return "Sorry, I couldn't connect to the booking service. Please check your connection and try again."
    except (ValueError, KeyError) as e:
        logger.error(f"Error processing booking data: {e}")
        return f"Sorry, there was an error processing the booking information: {str(e)}. Please check your details and try again."
    except Exception as e:
        logger.exception(f"Unexpected error while booking appointment: {e}")
        return "Sorry, an unexpected error occurred while booking the appointment. Please try again later."


@tool()
async def current_datetime_iso() -> str:
    """
    Returns the current date and time in ISO 8601 format.

    Use this tool whenever the agent needs the current date or time,
    including for scheduling, logging, comparisons, or time-based decisions.

    Returns:
        A string representing the current datetime in ISO 8601 format
        (e.g., '2026-01-04T10:56:17.100339+05:30').

    Constraints:
        This tool is the source of truth for the current time.
        Do not estimate or assume the current date or time without calling this tool.
    """

    return datetime.now().astimezone().isoformat()


async def get_event_type() -> List[dict[str, Any]]:
    """
    Returns the all event type.
    Returns:
        list[dict[str, Any]]: A list of all event types, one for each event type.
    """
    url = "https://api.cal.com/v2/event-types"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.API_KEY}",
        "cal-api-version": "2024-06-14"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                # Check HTTP status code
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    try:
                        error_data = await response.json()
                        error_message = error_data.get("message", error_data.get("error", "Unknown error"))
                    except:
                        error_message = error_text if error_text else "Unknown error"
                        logger.error(f"API error: {error_message}")

                    return []

                # Parse JSON response
                try:
                    data = await response.json()
                    logger.info(f"Booking response: {data}")
                except Exception as json_error:
                    logger.error(f"Failed to parse JSON response: {json_error}")
                    return []

                # Process successful response
                event_type = data.get("data", [])
                return event_type
    except Exception as e:
        logger.exception(f"Unexpected error while booking appointment: {e}")
        return []
