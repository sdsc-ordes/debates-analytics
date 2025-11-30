import logging
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from config.settings import get_settings
from routers import ingest, metadata, search, admin

settings = get_settings()

logging.basicConfig(
    level=settings.log_level.upper(),
    format='%(asctime)s - [%(levelname)s] - (%(filename)s:%(lineno)d) - %(funcName)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application is starting up...")
    logger.info(f"Loaded settings for environment: {settings.host}")
    yield
    logger.info("Application is shutting down...")

api = FastAPI(
    title="Debate Analytics API",
    lifespan=lifespan
)

api.include_router(
    ingest.router,
    tags=["Ingestion"]
)

api.include_router(
    metadata.router,
    tags=["Metadata"]
)

api.include_router(
    search.router,
    tags=["Search"]
)

api.include_router(
    admin.router,
    tags=["Admin"]
)



def serve():
    """
    Start the FastAPI server.
    """
    uvicorn.run(
        api,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    serve()
