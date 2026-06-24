# Karbuin v1.1.2 — multi-stage Docker build (optional)
#
# Engine FROZEN. Hanya containerization, no code changes.

FROM python:3.11.9-slim

# Labels
LABEL maintainer="Karbuin Curator <karbuin@karbuin.id>"
LABEL version="1.1.2"
LABEL description="Motorcycle Carburetor Diagnostic Expert System"

# Working dir
WORKDIR /app

# Copy source
COPY . /app/

# Persistent data directory
RUN mkdir -p /app/data/telemetry /app/data/cache /app/data/derived

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/motors').read()" || exit 1

# Run server (std-lib, no gunicorn needed)
CMD ["python3", "server.py", "--host", "0.0.0.0", "--port", "8000"]