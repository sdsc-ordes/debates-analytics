import logging
import uvicorn
import uuid
import time
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from config.settings import get_settings
from routers import ingest, metadata, search, admin
from fastapi.middleware.cors import CORSMiddleware
from config.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"System startup. Environment: {settings.host}")
    yield
    logger.info("System shutdown.")

api = FastAPI(
    title="Debate Analytics API",
    version="1.0.0",
    lifespan=lifespan
)

@api.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())

    logger.info(f"[{request_id}] >> {request.method} {request.url.path}")
    start_time = time.time()

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        response.headers["X-Request-ID"] = request_id

        logger.info(f"[{request_id}] << {response.status_code} ({process_time:.3f}s)")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"[{request_id}] !! 500 Internal Server Error ({process_time:.3f}s): {e}", exc_info=True)
        raise e


api.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
api.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
api.include_router(metadata.router, prefix="/db", tags=["Metadata"])
api.include_router(search.router, prefix="/search", tags=["Search"])
api.include_router(admin.router, prefix="/admin", tags=["Admin"])

def serve():
    """Entrypoint for the application"""
    # 5. Use Import String for Uvicorn
    # Passing "main:api" instead of the object allows Uvicorn to use workers/reload
    uvicorn.run(
        "main:api",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    serve()
