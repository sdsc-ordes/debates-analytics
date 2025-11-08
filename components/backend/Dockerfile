FROM docker.io/library/python:3.11-slim

RUN pip install uv

WORKDIR /app
COPY src pyproject.toml README.md uv.lock ./

RUN uv sync --no-cache

EXPOSE 8000

CMD ["python", "debates.py", "serve"]
