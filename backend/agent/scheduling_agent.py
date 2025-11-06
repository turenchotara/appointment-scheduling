from langchain.chat_models import init_chat_model
from langchain.messages import ToolMessage
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from backend.agent.state import MessagesState
from backend.tools import book_appointment, check_availability

model = init_chat_model(
    # "google_vertexai:gemini-2.5-flash",
    "",
    temperature=0.2
)

tools = [book_appointment, check_availability]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)


def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with performing operation like book appointment or give FAQ answer based on user query."
                    )
                ]
                + state["messages"]
            )
        ],
        "session_id": state["session_id"]
    }

def tool_node(state: dict):
    """Performs the tool call"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}


# Build workflow
agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_edge("llm_call", END)

# Compile the agent
agent = agent_builder.compile()


def invoke_agent(query, session_id):
    messages = [HumanMessage(content=query)]
    messages = agent.invoke({"messages": messages, "session_id": session_id})
    for m in messages["messages"]:
        m.pretty_print()
    return messages["messages"]