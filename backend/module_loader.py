import importlib
import time
from typing import Sequence

from .logging_config import logger


def load_modules(modules: Sequence[str]) -> None:
    """Dynamically load and initialize backend modules.
    
    Args:
        modules: Sequence of module names to import.
    """
    for module in modules:
        try:
            st_time: float = time.time()
            importlib.import_module(module)
            elapsed: float = time.time() - st_time
            logger.info(f"Loaded module >>> {module} time ::: {elapsed:.4f}s")
        except Exception as e:
            logger.error(f"Failed to load module {module}: {e}")
