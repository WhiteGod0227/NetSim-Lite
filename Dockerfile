# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/index.html frontend/tsconfig.json frontend/vite.config.ts ./
COPY frontend/src ./src
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0 \
    NETSIM_STATIC_DIR=/app/frontend/dist
WORKDIR /app
COPY backend/requirements-production.txt ./backend/requirements-production.txt
RUN pip install --no-cache-dir -r backend/requirements-production.txt \
    && groupadd --gid 10001 netsim \
    && useradd --uid 10001 --gid netsim --no-create-home netsim
COPY backend ./backend
COPY --from=frontend /build/frontend/dist ./frontend/dist
USER netsim
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/api/health',timeout=3)" || exit 1
CMD ["python", "-m", "backend.production"]
