FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONPATH=/app/backend

WORKDIR /app

COPY backend/requirements-runtime.txt /app/requirements-runtime.txt

RUN pip install --upgrade pip && \
    pip install -r /app/requirements-runtime.txt

COPY alembic.ini /app/alembic.ini
COPY backend /app/backend

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn search_api.main:app --host 0.0.0.0 --port 8000"]