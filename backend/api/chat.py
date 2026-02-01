from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from backend import logger
from backend.agent import invoke_agent
from backend.agent.state import AgentResponse
from backend.rag.faq import FAQ
from . import app_router


@app_router.get("/")
async def read_root() -> dict[str, str]:
    """Root endpoint returning a welcome message.
    
    Returns:
        A dictionary with a welcome message.
    """
    return {"message": "Hello, FastAPI!"}


@app_router.get("/chat")
async def read_item(user_query: str, session_id: str) -> dict[str, AgentResponse | str]:
    """Process a chat message from the user.
    
    Args:
        user_query: The user's input message.
        session_id: Unique identifier for the conversation session.
        
    Returns:
        A dictionary containing the agent's response.
        
    Raises:
        HTTPException: If validation fails or an internal error occurs.
    """
    try:
        if not user_query or not user_query.strip():
            raise HTTPException(
                status_code=400, 
                detail="user_query parameter is required and cannot be empty"
            )
        
        if not session_id or not session_id.strip():
            raise HTTPException(
                status_code=400, 
                detail="session_id parameter is required and cannot be empty"
            )
        
        logger.info(f"Processing chat request for session {session_id}: {user_query[:100]}")
        result: AgentResponse = await invoke_agent(user_query, session_id)
        
        if result is None:
            logger.warning(f"Agent returned None for session {session_id}")
            return {"result": "Sorry, I couldn't process your request. Please try again."}
        
        return {"result": result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing your request. Please try again later."
        )


@app_router.post("/training-faq")
async def train_faq() -> JSONResponse:
    """Train/index the FAQ knowledge base.
    
    Returns:
        JSONResponse with success message.
        
    Raises:
        HTTPException: If training fails.
    """
    try:
        await FAQ().index_faqs()
        return JSONResponse(
            status_code=200,
            content={"message": "FAQ train successfully"}
        )
    except Exception as e:
        logger.exception(f"Error training FAQ: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while training the FAQ. Please check the logs for details."
        )


@app_router.get("/search-faq/{query}")
async def search_faq(query: str) -> dict[str, str]:
    """Search the FAQ knowledge base for relevant answers.
    
    Args:
        query: The search query string.
        
    Returns:
        A dictionary containing the FAQ response.
        
    Raises:
        HTTPException: If validation fails or search encounters an error.
    """
    try:
        if not query or not query.strip():
            raise HTTPException(
                status_code=400, 
                detail="query parameter is required and cannot be empty"
            )
        
        logger.info(f"Searching FAQ for: {query}")
        response: str = FAQ().answer_faq_query(query)
        
        if response is None:
            return {"response": "No relevant FAQ found for your query."}
        
        return {"response": response}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error searching FAQ: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while searching the FAQ. Please try again later."
        )
