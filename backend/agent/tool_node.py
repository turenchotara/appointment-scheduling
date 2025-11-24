from typing import Dict, List

from langchain.messages import ToolMessage
from langchain_core.messages import AIMessage

from backend.tools import tools_by_name


def tool_node(state: Dict) -> Dict[str, List[ToolMessage]]:
    """Execute pending tool calls emitted by the LLM."""
    if not state["messages"]:
        return {}

    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage):
        return {}

    tool_calls = getattr(last_message, "tool_calls", None)
    if not tool_calls:
        return {}

    observations = []
    for tool_call in tool_calls:
        tool = tools_by_name[tool_call["name"]]
        result = tool.invoke(tool_call["args"])
        observations.append(
            ToolMessage(content=result, tool_call_id=tool_call["id"])
        )

    return {"messages": observations}

