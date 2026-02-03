from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import END, START
from langgraph.graph import StateGraph

from backend import logger
from backend.tools import tools
from .llm_config import get_llm_with_tools
from .prompt import AGENT_PROMPT
from .state import AgentResponse, MessagesState
from .tool_node import tool_node

# Get the LLM with tools bound
model_with_tools = get_llm_with_tools(tools, provider="gemini")


def llm_call(state: MessagesState) -> MessagesState:
    """LLM decides whether to call a tool or not.
    
    Args:
        state: The current agent state containing messages.
        
    Returns:
        Updated state with the LLM response.
    """
    llm_response = model_with_tools.invoke(
        [SystemMessage(content=AGENT_PROMPT)] + state["messages"]
    )

    return {
        "messages": [llm_response],
        "session_id": state["session_id"]
    }


def should_continue(state: MessagesState) -> Literal["tool_node", "end"]:
    """Decide whether we need to execute a tool call.
    
    Args:
        state: The current agent state containing messages.
        
    Returns:
        "tool_node" if there are tool calls to execute, "end" otherwise.
    """
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tool_node"
    return "end"


# Build workflow
agent_builder: StateGraph = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        "tool_node": "tool_node",
        "end": END
    }
)
agent_builder.add_edge("tool_node", "llm_call")

checkpointer: InMemorySaver = InMemorySaver()
# Compile the agent
agent = agent_builder.compile(checkpointer=checkpointer)


async def invoke_agent(query: str, session_id: str) -> AgentResponse:
    """Invoke the scheduling agent with a user query.
    
    Args:
        query: The user's input message.
        session_id: Unique identifier for the conversation session.
        
    Returns:
        AgentResponse containing the message and reason.
    """
    messages = [HumanMessage(content=query)]
    result = await agent.ainvoke(
        {"messages": messages, "session_id": session_id},
        config={"configurable": {"thread_id": session_id}}
    )
    
    logger.info("Agent invocation complete.")
    response: AgentResponse = {"msg": "", "reason": ""}
    
    last_msg = result["messages"][-1]
    last_msg.pretty_print()
    
    if isinstance(last_msg, AIMessage):
        if getattr(last_msg, "tool_calls", None) and not response["reason"]:
            response["reason"] = str(last_msg.content)
        response["msg"] = last_msg.text if hasattr(last_msg, "text") else str(last_msg.content)

    if not response["reason"]:
        response["reason"] = response["msg"]
    
    return response
