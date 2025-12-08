import importlib
import logging
import time

from fastapi import FastAPI

from .settings import settings


class ColorFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[1;31m'  # Bold Red
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        message = super().format(record)
        return f"{log_color}{message}{self.RESET}"


handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter("%(levelname)-8s | %(message)s"))

logger = logging.getLogger("appointment-scheduling-agent")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

for module in settings.BACKEND_MODULES:
    try:
        st_time = time.time()
        importlib.import_module(module)
        logger.info(f"Loaded module >>> {module} time ::: {time.time()-st_time}")
    except Exception as e:
        logger.error(f"Failed to load module {module}: {e}")

from backend.api import calendly_router, app_router

app = FastAPI()
app.include_router(app_router)
app.include_router(calendly_router)
