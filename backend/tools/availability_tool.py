from datetime import datetime
from typing import Any

import aiohttp
from langchain.tools import tool
from pydantic import BaseModel, Field

from backend import logger, settings

# Type aliases
APIResponse = dict[str, Any]
SlotData = dict[str, list[dict[str, str]]]


class Availability(BaseModel):
    """Schema for availability check parameters."""
    
    session_type: str = Field(
        ..., 
        description="Type of the session which need to check for availability"
    )
    session_date: str = Field(
        ..., 
        description="Date of the session for which availability needs to be checked in YYYY-MM-DD format"
    )


@tool(args_schema=Availability)
async def check_availability(session_type: str, session_date: str) -> str:
    """Check availability of appointment slots for a given session type and date.
    
    This tool checks the Cal.com API for available time slots.
    
    Args:
        session_type: Type of the session to check availability for.
        session_date: Date in YYYY-MM-DD format.
        
    Returns:
        A string with available time slots or an error message.
    """
    logger.info(f"Checking availability for {session_type} on {session_date}...")
    
    headers: dict[str, str] = {
        "Authorization": f"Bearer {settings.API_KEY}",
        "cal-api-version": "2024-09-04",
        "Content-Type": "text/plain"
    }
    url: str = "https://api.cal.com/v2/slots"
    
    try:
        async with aiohttp.ClientSession() as session:
            params: dict[str, str] = {
                "eventTypeSlug": session_type,
                "username": "turen",
                "start": session_date,
                "end": session_date,
                "timeZone": "Asia/Kolkata"
            }
            async with session.get(
                url, 
                headers=headers, 
                params=params, 
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                # Check HTTP status code
                if response.status >= 400:
                    error_text: str = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    
                    if response.status == 401:
                        return "Sorry, I'm unable to check availability due to authentication issues. Please contact support."
                    elif response.status == 404:
                        return f"Sorry, I couldn't find availability for session type '{session_type}'. Please check if the session type is correct."
                    elif response.status == 429:
                        return "Sorry, too many requests. Please try again in a moment."
                    elif response.status >= 500:
                        return "Sorry, the availability service is currently unavailable. Please try again later."
                    else:
                        return f"Sorry, I encountered an error while checking availability (status {response.status}). Please try again."
                
                # Parse JSON response
                try:
                    result: APIResponse = await response.json()
                except Exception as json_error:
                    logger.error(f"Failed to parse JSON response: {json_error}")
                    return "Sorry, I received an invalid response from the availability service. Please try again."
                
                # Process successful response
                if result.get("status") == 'success':
                    data: SlotData = result.get('data', {})
                    if session_date in data and data[session_date]:
                        try:
                            time_slots: list[str] = [
                                datetime.fromisoformat(rs['start']).strftime("%H:%M") 
                                for rs in data[session_date]
                            ]
                            return f"Here are available slots for appointments on {session_date}:\n" + "\n".join(time_slots)
                        except (KeyError, ValueError, TypeError) as parse_error:
                            logger.error(f"Error parsing time slots: {parse_error}")
                            return "Sorry, I couldn't parse the available time slots. Please try again."
                    else:
                        return f"Sorry, no available slots found for {session_type} on {session_date}."
                else:
                    error_message: str = result.get("message", "Unknown error")
                    logger.warning(f"API returned non-success status: {error_message}")
                    return f"Sorry, I couldn't retrieve availability information. {error_message}"
                    
    except aiohttp.ClientTimeout:
        logger.error("Request timeout while checking availability")
        return "Sorry, the request timed out while checking availability. Please try again."
    except aiohttp.ClientResponseError as e:
        logger.error(f"Client response error: {e.status} - {e.message}")
        return f"Sorry, I encountered an error from the availability service (status {e.status}). Please try again."
    except aiohttp.ClientError as e:
        logger.error(f"Client error while checking availability: {e}")
        return "Sorry, I couldn't connect to the availability service. Please check your connection and try again."
    except Exception as e:
        logger.exception(f"Unexpected error while checking availability: {e}")
        return "Sorry, an unexpected error occurred while checking availability. Please try again later."


@tool
def appointment_session_types() -> str:
    """Retrieve all available appointment session types and their durations.
    
    Call this when you need to know what types of appointments can be booked
    or to calculate time slots.

    Returns:
        A string listing available appointment session types with durations.
    """
    durations: dict[str, int] = {
        "consultation": 30,
        "followup": 15,
        "physical": 45,
        "specialist": 60
    }
    logger.info("Fetch appointment types.")
    return "Here are the available appointment session type:\n" + "\n".join(
        f"{k}: {v} mins" for k, v in durations.items()
    )
