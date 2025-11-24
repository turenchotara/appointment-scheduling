from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from .prompt import AGENT_PROMPT
from .state import MessagesState
from .tool_node import tool_node
from backend.tools import tools

from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="",
    temperature=0,
    max_retries=2,
    google_api_key=""
)

model_with_tools = llm.bind_tools(tools)


def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""

    llm_response = model_with_tools.invoke(
        [
            SystemMessage(
                content=AGENT_PROMPT
            )
        ]
        + state["messages"]
    )

    return {
        "messages": [llm_response],
        "session_id": state["session_id"]
    }


def should_continue(state: dict) -> str:
    """Decide whether we need to execute a tool call."""
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tool_node"
    return "end"


# Build workflow
agent_builder = StateGraph(MessagesState)

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

# Compile the agent
agent = agent_builder.compile()


def invoke_agent(query, session_id):
    messages = [HumanMessage(content=query)]
    messages = agent.invoke({"messages": messages, "session_id": session_id})
    response = {"msg": "", "reason": ""}
    for m in messages["messages"]:
        m.pretty_print()
        if isinstance(m, AIMessage):
            if getattr(m, "tool_calls", None) and not response["reason"]:
                response["reason"] = m.content
            response['msg'] = m.content
    if not response["reason"]:
        response["reason"] = response["msg"]
    return response