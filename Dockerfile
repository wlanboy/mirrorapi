ARG PYTHON_TAG=3.15-slim

# Build stage
FROM python:${PYTHON_TAG} AS build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --only-binary=:all: -r requirements.txt


# Runtime stage
FROM python:${PYTHON_TAG}
ARG REVISION=unknown
LABEL org.opencontainers.image.title="mirrorapi" \
      org.opencontainers.image.description="REST-API zum Testen von HTTP-Clients: spiegelt Requests, simuliert Status-Codes und Verzögerungen, speichert Mocks" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.vendor="wlanboy" \
      org.opencontainers.image.source="https://github.com/wlanboy/mirrorapi" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.base.name="python:3.15-slim"
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# System user without home and login shell, UID/GID 1000 as in the Helm chart
RUN groupadd -r -g 1000 appuser && useradd -r -u 1000 -g appuser appuser

WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY --chown=appuser:appuser *.py /app/

USER appuser
EXPOSE 4500

# --no-server-header: do not reveal "server: uvicorn" in responses
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4500", "--no-server-header"]
