# Use the Python version specified in your pyproject.toml
FROM python:3.11-slim

# 1. Install system deps (FFmpeg) and uv in one layer
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/* && \
    pip install uv

WORKDIR /app

# 2. Set up venv (good practice, matches medialoader)
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 3. Copy *only* dependency files
COPY pyproject.toml uv.lock ./

# 4. Install dependencies
# This step will be cached as long as uv.lock doesn't change
RUN uv sync --frozen --no-cache

# 3. Copy the entire source code directory
# This ensures flows.py is available at /app/src/flows.py
COPY src/ .

# CRITICAL FIX: Add the application directory to the Python path
# This allows the worker to run: import src.flows
ENV PYTHONPATH=/app:$PYTHONPATH

# 4. Set the container entrypoint to the 'prefect' executable
ENTRYPOINT ["prefect"]

# 5. Default command for the worker (to be run by docker compose)
CMD ["worker", "start", "--pool", "default-agent-pool"]