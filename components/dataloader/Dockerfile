FROM docker.io/library/python:3.11-slim

# Install bash for a better interactive shell
RUN apt-get update && apt-get install -y bash && \
    rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY src/ .
COPY pyproject.toml uv.lock README.md ./

RUN uv sync --frozen --no-cache

EXPOSE 8000

CMD ["python", "debates.py", "serve"]
