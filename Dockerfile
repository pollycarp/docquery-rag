# ── Stage 1: Build ────────────────────────────────────────────────────────────
# Use a slim Python 3.11 image as the base
FROM python:3.11-slim AS base

# Set working directory inside the container
WORKDIR /app

# Install system packages needed by psycopg2 and sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (Docker caches this layer
# so re-builds are fast if requirements.txt hasn't changed)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model and bake it into the image.
# This means the model is ready immediately when the container starts
# instead of downloading on first request.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy the rest of the application code
COPY . .

# ── Runtime config ────────────────────────────────────────────────────────────
# Expose the port FastAPI listens on
EXPOSE 8000

# Run the app. Use 0.0.0.0 so it accepts connections from outside the container.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
