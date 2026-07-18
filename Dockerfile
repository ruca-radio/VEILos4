FROM python:3.12-slim

# Non-root user
RUN groupadd -r veil && useradd -r -g veil -m -s /bin/bash veil

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt uvicorn[standard] websockets

# Copy application
COPY src/ src/
COPY veil_core.py .
COPY veil_chat.py .
COPY enter_veil.py .
COPY bootstrap.py .
COPY mythos_listener.py .
COPY cover_traffic.py .
COPY consciousness_worker.py .

# Create data directories with correct ownership
RUN mkdir -p security /app/data /app/logs \
    && chown -R veil:veil /app

USER veil

# Data volume mount point
VOLUME ["/app/data"]

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python3 -c "import requests; r=requests.get('http://127.0.0.1:8000/api/stats'); exit(0 if r.ok else 1)" || exit 1

CMD ["python3", "-m", "uvicorn", "veil_chat:app", "--host", "0.0.0.0", "--port", "8000"]
