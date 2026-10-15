FROM node:22-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS api
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-hin tesseract-ocr-kan tesseract-ocr-tam \
    tesseract-ocr-tel tesseract-ocr-fra tesseract-ocr-spa tesseract-ocr-deu \
    libglib2.0-0 libgomp1 && rm -rf /var/lib/apt/lists/*
COPY requirements-api.txt requirements-api.lock ./
RUN pip install --no-cache-dir -r requirements-api.lock
ARG INSTALL_ML=false
COPY requirements-ml.txt ./
RUN if [ "$INSTALL_ML" = "true" ]; then pip install --no-cache-dir -r requirements-ml.txt; fi
COPY backend ./backend
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/health/live', timeout=3)"
CMD ["python", "-m", "backend.serve"]

# Default target: one full-stack service for VibeNest and similar Docker hosts.
FROM api AS standalone
COPY --from=frontend-build /frontend/dist /app/frontend-dist
ENV FRONTEND_DIST=/app/frontend-dist
