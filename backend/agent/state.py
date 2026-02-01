import operator
from typing import Annotated

from langchain_core.messages import AnyMessage
from typing_extensions import TypedDict


class MessagesState(TypedDict):
    """State container for agent messages and session tracking."""
    
    messages: Annotated[list[AnyMessage], operator.add]
    session_id: str


class AgentResponse(TypedDict):
    """Response structure returned by the agent."""
    
    msg: str
    reason: str
