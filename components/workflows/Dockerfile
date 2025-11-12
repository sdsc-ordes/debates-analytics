# Use the Python version specified in your pyproject.toml
FROM python:3.11-slim

# Install uv globally for environment management
RUN pip install uv

WORKDIR /app

# 1. Copy dependency files (pyproject.toml and uv.lock for fast, locked install)
COPY pyproject.toml uv.lock /app/

# 2. Compile and Install dependencies using uv
# --no-deps prevents installing transitive dependencies from lock if it's there
# We install from the lock file for speed and exact reproducibility
RUN uv pip install --all-features --locked --no-deps -f uv.lock \
    && rm -rf /root/.cache/uv

# 3. Copy the entire source code directory
# This ensures flows.py is available at /app/src/flows.py
COPY src /app/src 

# CRITICAL FIX: Add the application directory to the Python path
# This allows the worker to run: import src.flows
ENV PYTHONPATH=/app:$PYTHONPATH

# 4. Set the container entrypoint to the 'prefect' executable
ENTRYPOINT ["prefect"]

# 5. Default command for the worker (to be run by docker compose)
CMD ["worker", "start", "--pool", "default-agent-pool"]