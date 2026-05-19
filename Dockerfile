# ---- Stage 1: Build frontend ----
FROM node:20-alpine AS frontend-build

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ---- Stage 2: Production image ----
FROM python:3.11-slim

WORKDIR /app

# System dependencies: nginx + ffmpeg + mediainfo + supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    ffmpeg \
    mediainfo \
    supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

# Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Backend code
COPY backend/ /app/backend/

# Frontend build output
COPY --from=frontend-build /app/dist /usr/share/nginx/html

# Nginx config (production)
COPY docker/nginx.prod.conf /etc/nginx/conf.d/default.conf

# Supervisor config
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create data directory
RUN mkdir -p /app/backend/data

# Default environment variables
ENV DATABASE_URL=sqlite+aiosqlite:///app/backend/data/asmr_manager.db
ENV DOWNLOAD_DIR=/media/downloads
ENV LIBRARY_DIR=/media/library

EXPOSE 80

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
