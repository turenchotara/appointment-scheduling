from .settings import settings
from .logging_config import logger
from .module_loader import load_modules

# Load backend modules dynamically
load_modules(settings.BACKEND_MODULES)

# Import routers after modules are loaded
from .api import app_router, calendly_router
from .app_factory import create_app

# Create the FastAPI application
app = create_app()

__all__ = [
    "app",
    "app_router",
    "calendly_router",
    "create_app",
    "logger",
    "load_modules",
    "settings",
]
