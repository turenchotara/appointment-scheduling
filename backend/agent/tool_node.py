from typing import Any

from langchain_core.messages import AIMessage, ToolMessage

from backend import logger
from backend.tools import tools_by_name
from .state import MessagesState


async def tool_node(state: MessagesState) -> dict[str, list[ToolMessage]]:
    """Execute pending tool calls emitted by the LLM.
    
    Args:
        state: The current agent state containing messages.
        
    Returns:
        A dictionary with the tool message observations.
    """
    logger.info("Starting tool node")
    
    if not state["messages"]:
        return {"messages": []}

    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage):
        return {"messages": []}

    tool_calls: list[dict[str, Any]] | None = getattr(last_message, "tool_calls", None)
    if not tool_calls:
        return {"messages": []}

    observations: list[ToolMessage] = []
    for tool_call in tool_calls:
        tool_name: str = tool_call["name"]
        tool_id: str = tool_call["id"]
        tool_args: dict[str, Any] = tool_call["args"]
        
        logger.info(f"Calling.... {tool_name}")
        logger.debug(f"Tool call info :::\t{tool_call}")
        
        tool = tools_by_name[tool_name]

        try:
            result: str = await tool.ainvoke(tool_args)
            observations.append(
                ToolMessage(content=result, tool_call_id=tool_id)
            )
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            observations.append(
                ToolMessage(content=str(e), tool_call_id=tool_id)
            )
        
        for observation in observations:
            observation.pretty_print()

    return {"messages": observations}
