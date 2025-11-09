FROM docker.io/library/python:3.11-slim

# Install uv
RUN pip install uv

WORKDIR /app

# Set up venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# Copy source code
COPY src/ .

# Run the script
CMD ["python", "transcribe_worker.py"]
