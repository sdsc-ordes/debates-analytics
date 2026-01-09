import logging
from config.settings import get_settings

def configure_logging():
    settings = get_settings()

    logging.basicConfig(
        level=settings.log_level.upper(),
        format='%(asctime)s - [%(levelname)s] - (%(filename)s:%(lineno)d) - %(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Lower the noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
