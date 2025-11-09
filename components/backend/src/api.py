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
    Start the FastAPI server.
    """
    uvicorn.run(api, port=8001)


if __name__ == "__main__":
    serve()
