FROM docker.io/library/python:3.11-slim

RUN apt-get update && \
    apt-get install -y bash && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/* && \
    pip install uv


RUN pip install uv

WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./

RUN uv sync --frozen --no-cache

COPY src/ .
