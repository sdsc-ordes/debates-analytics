import logging
import sys
from config.settings import get_settings

from contextvars import ContextVar

# 1. Define the ContextVar (This is the "Magic Container")
# It holds the ID specifically for the current running task/request.
request_id_context = ContextVar("request_id", default=None)

class RequestIDFilter(logging.Filter):
    """
    This filter runs on EVERY log message.
    It grabs the current ID from the context and adds it to the log record.
    """
    def filter(self, record):
        # Get the ID, or use "SYSTEM" if we are outside a request (e.g. startup)
        record.request_id = request_id_context.get() or "SYSTEM"
        return True

def configure_logging():
    settings = get_settings()
    # Define the format. We added [%(request_id)s] here.
    log_format = (
        '%(asctime)s - [%(levelname)s] - [%(request_id)s]'
        '(%(filename)s:%(lineno)d) - %(funcName)s - \n%(message)s'
    )

    # Create the handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S'))

    # Create the filter instance
    request_id_filter = RequestIDFilter()
    handler.addFilter(request_id_filter)

    # Apply to root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())
    root_logger.handlers = [handler]

    # Silence uvicorn's default noise so we don't get duplicate logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
