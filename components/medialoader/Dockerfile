FROM docker.io/library/python:3.11-slim

# 1. Install system deps (FFmpeg) and uv in one layer
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/* && \
    pip install uv

WORKDIR /app

# 2. Set up venv (good practice, matches dataloader)
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 3. Copy *only* dependency files
COPY pyproject.toml uv.lock ./

# 4. Install dependencies
# This step will be cached as long as uv.lock doesn't change
RUN uv sync --frozen --no-cache

# 5. Copy your source code
# This copies 'src/converter.py' to '/app/converter.py'
COPY src/ .

# 6. Run the script (this command is the same as before)
CMD ["python", "medialoader_producer.py"]
