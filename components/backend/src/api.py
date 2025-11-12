import typer
import uvicorn
import os
from dotenv import load_dotenv
from backend.api import api

load_dotenv()


cli = typer.Typer()

@cli.command()
def serve():
    """
    Start the FastAPI server listening on 0.0.0.0.
    """
    # NOTE: It's best practice to pass the app target as a string
    # when running from a script, but we can also stick to the object
    # for simplicity if not using the uvicorn CLI directly.

    # We'll use the object, but add the necessary host/port arguments
    uvicorn.run(
        api,
        host="0.0.0.0",  # LISTEN ON ALL INTERFACES FOR DOCKER
        port=8000,       # Set the internal container port
        log_level="info"
    )

if __name__ == "__main__":
    serve()
