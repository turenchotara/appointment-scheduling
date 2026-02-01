import logging
from typing import ClassVar


class ColorFormatter(logging.Formatter):
    """Custom formatter that adds color coding to log messages based on level."""
    
    COLORS: ClassVar[dict[str, str]] = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[1;31m' # Bold Red
    }
    RESET: ClassVar[str] = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with color coding.
        
        Args:
            record: The log record to format.
            
        Returns:
            The formatted log message with ANSI color codes.
        """
        log_color: str = self.COLORS.get(record.levelname, self.RESET)
        message: str = super().format(record)
        return f"{log_color}{message}{self.RESET}"


def setup_logger(name: str = "appointment-scheduling-agent") -> logging.Logger:
    """Set up and configure the application logger.
    
    Args:
        name: The name for the logger instance.
        
    Returns:
        Configured logger instance.
    """
    handler: logging.StreamHandler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter("%(levelname)-8s | %(message)s"))

    logger: logging.Logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid adding duplicate handlers
    if not logger.handlers:
        logger.addHandler(handler)
    
    return logger


# Create the default logger instance
logger: logging.Logger = setup_logger()
