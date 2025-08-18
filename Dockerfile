FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONOPTIMIZE=1

# Create non-root user
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

# Install backend dependencies first for better layer cache
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip wheel setuptools && \
    pip install -r /tmp/requirements.txt

# Copy backend code
COPY --chown=app:app backend /app

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


