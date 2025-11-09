import typer
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

API_HOST = os.getenv("API_HOST")


cli = typer.Typer()


@cli.command()
def serve():
    """
    Start the FastAPI server.
    """
    uvicorn.run(api, host=API_HOST, port=8000)


if __name__ == "__main__":
    cli()
