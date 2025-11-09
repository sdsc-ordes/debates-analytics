FROM docker.io/library/python:3.11-slim

# Install bash for a better interactive shell
RUN apt-get update && apt-get install -y bash && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

WORKDIR /app

# Set up the virtual environment variables explicitly
# This tells Python to use the venv created by uv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy files
# Using "src/ ." copies the *contents* of src to /app,
# so debates.py ends up at /app/debates.py
COPY src/ .
COPY pyproject.toml README.md uv.lock ./

# Install dependencies into the environment set up above
RUN uv sync --frozen --no-cache

EXPOSE 8000

# Now 'python' will automatically use the .venv
CMD ["python", "debates.py", "serve"]
