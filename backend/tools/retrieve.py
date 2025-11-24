from langchain.tools import tool
from pydantic import BaseModel, Field

from backend.rag.faq import FAQ


class Retrieve(BaseModel):
    query: str = Field(
        ...,
        description="The user's question or information request that needs to be answered using the FAQ knowledge base. This should be the exact question or query as asked by the user."
    )


@tool(args_schema=Retrieve)
def get_relevant_faq(query: str):
    """
    Retrieves relevant FAQ entries and knowledge base information to answer user questions.
    
    Use this tool when:
    - You need factual information from the knowledge base to provide accurate answers
    - The user's question cannot be answered with just appointment availability or booking actions
    
    This tool searches the vector database for the most relevant FAQ entries and returns them
    as context to help formulate a comprehensive answer.
    
    Args:
        query: The user's question or information request to search for in the FAQ knowledge base.
    
    Returns:
        A string containing the most relevant FAQ entries and knowledge chunks, separated by newlines.
    """

    return FAQ().answer_faq_query(query)
