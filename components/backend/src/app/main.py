import logging
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

# 1. Import your settings
from common.config import get_settings

# 2. Import your separate router files
# (Make sure your routers folder has an __init__.py file, even if empty)
from routers import ingest, metadata, search

# Load settings once
settings = get_settings()

# --- Logging Setup ---
# We use the log_level from our settings (config.py)
logging.basicConfig(
    level=settings.log_level.upper(), # Ensure it is uppercase (INFO, DEBUG)
    format='%(asctime)s - [%(levelname)s] - (%(filename)s:%(lineno)d) - %(funcName)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Lifecycle (Optional but recommended) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic (e.g. check DB connection)
    logger.info("Application is starting up...")
    logger.info(f"Loaded settings for environment: {settings.host}")
    yield
    # Shutdown logic
    logger.info("Application is shutting down...")

# --- App Definition ---
api = FastAPI(
    title="Debate Analytics API",
    lifespan=lifespan
)

# --- 3. THE MISSING PIECE: Register the Routers ---

# Ingest Routes (e.g., POST /ingest/get-presigned-post)
api.include_router(
    ingest.router,
    tags=["Ingestion"]
    # Note: If you want a prefix, add prefix="/ingest" here
)

# Debate Routes (e.g., POST /debates/get-metadata)
api.include_router(
    metadata.router,
    tags=["Metadata"]
)

# Search Routes (e.g., POST /search/search-solr)
api.include_router(
    search.router,
    tags=["Search"]
)


def serve():
    """
    Start the FastAPI server.
    """
    # Use settings for host/port
    uvicorn.run(
        api,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    serve()
