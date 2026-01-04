from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from backend.tools import tools
from .prompt import AGENT_PROMPT
from .state import MessagesState
from .tool_node import tool_node
from backend import logger

gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.1,
    max_retries=2,
    google_api_key=""
)

azure_openai_llm = AzureChatOpenAI(
    azure_endpoint="",
    azure_deployment="gpt-4.1",
    api_key="",
    api_version=""
)

model_with_tools = azure_openai_llm.bind_tools(tools)


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

checkpointer = InMemorySaver()
# Compile the agent
agent = agent_builder.compile(checkpointer=checkpointer)


async def invoke_agent(query, session_id):
    messages = [HumanMessage(content=query)]
    messages = await agent.ainvoke({"messages": messages, "session_id": session_id},
                            config={"configurable": {"thread_id": session_id}}
                            )
    logger.info("Agent invocation complete.")
    response = {"msg": "", "reason": ""}
    last_msg = messages["messages"][-1]
    last_msg.pretty_print()
    if isinstance(last_msg, AIMessage):
        if getattr(last_msg, "tool_calls", None) and not response["reason"]:
            response["reason"] = last_msg.content
        response['msg'] = last_msg.text

    if not response["reason"]:
        response["reason"] = response["msg"]
    return response
