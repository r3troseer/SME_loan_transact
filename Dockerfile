# Combined Dockerfile for Railway deployment
# Builds frontend and serves via FastAPI backend

# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source
COPY frontend/ .

# Build frontend
RUN npm run build

# Stage 2: Python backend with static files
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/app ./app

# Copy data files (Excel source data)
COPY data ./data

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./static

# Create data directory for SQLite
RUN mkdir -p /app/data

# Set environment variables
ENV PORT=8000
ENV DATABASE_URL=sqlite:///./data/gfa.db

# Expose port (Railway uses PORT env var)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Create startup script that runs migration then starts server
RUN echo '#!/bin/bash\n\
python -m app.services.data_loader 2>/dev/null || echo "Migration skipped or already done"\n\
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}' > /app/start.sh && chmod +x /app/start.sh

# Run the application
CMD ["/bin/bash", "/app/start.sh"]
