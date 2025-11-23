import typer
import uvicorn
import os
from dotenv import load_dotenv
from backend.api import api

load_dotenv()


def serve():
    """
    Start the FastAPI server.
    """
    uvicorn.run(
        api,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    serve()
