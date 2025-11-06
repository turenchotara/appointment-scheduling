from fastapi import APIRouter

calendly_router = APIRouter(prefix="/api/calendly", tags=["calendly"])
app_router = APIRouter(tags=["app"])

from . import chat, calendly_integration
