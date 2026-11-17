# Build stage
FROM python:3.15-slim AS builder

WORKDIR /build

# Install dependencies into virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Runtime stage
FROM python:3.15-slim AS runtime

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code owned by the non-root user
COPY --chown=appuser:appuser *.py /app/

USER appuser

EXPOSE 4500

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4500"]
