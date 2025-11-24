from .booking_tool import book_appointment
from .availability_tool import check_availability
from .retrieve import get_relevant_faq

tools = [book_appointment, check_availability, get_relevant_faq]
tools_by_name = {tool.name: tool for tool in tools}


__all__ = [
    # 'book_appointment',
    # 'check_availability',
    # 'get_relevant_faq',
    'tools',
    'tools_by_name'
]