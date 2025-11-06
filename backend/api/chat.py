from fastapi.responses import JSONResponse

from backend.models.schema import ChatRequest
from backend.rag.faq import FAQ
from .. import logger
from ..agent import invoke_agent
from ..api import app_router


@app_router.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}


@app_router.get("/chat")
async def read_item(request_data: ChatRequest):
    result = invoke_agent(request_data.user_query, request_data.session_id)
    return {"result": result}


@app_router.post("/training-faq")
async def train_faq():
    await FAQ().index_faqs()
    return JSONResponse(
        status_code=200,
        content={"message": "FAQ train successfully"})


@app_router.get("/search-faq/{query}")
async def train_faq(query: str):
    logger.info(f"{query} for searching..")
    response = FAQ().answer_faq_query(query)
    return {"response": response}
