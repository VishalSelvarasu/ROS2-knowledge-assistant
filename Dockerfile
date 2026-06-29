FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/
COPY docs/ ./docs/

# Default: run the FastAPI server
# Override CMD in docker-compose for MCP server or ingest
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
