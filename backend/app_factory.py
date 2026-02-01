from fastapi import FastAPI

from .api import app_router, calendly_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance.
    """
    app: FastAPI = FastAPI(
        title="Appointment Scheduling API",
        description="AI-powered appointment scheduling assistant",
        version="1.0.0"
    )
    
    app.include_router(app_router)
    app.include_router(calendly_router)
    
    return app
