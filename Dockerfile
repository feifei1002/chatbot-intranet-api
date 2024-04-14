FROM python:3.11-slim

WORKDIR /app/

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
     pip install -r requirements.txt

RUN --mount=type=cache,target=/var/cache/apt \
    playwright install chromium && \
    rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EXPOSE 8000
