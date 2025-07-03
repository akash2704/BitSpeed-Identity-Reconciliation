FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

RUN pip install uv --no-cache-dir

ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked
COPY main.py ./


# Expose the port (change to 8002 as in your example)
EXPOSE 8002

# Use gunicorn to serve the Flask app
CMD ["/app/.venv/bin/gunicorn", "--bind", "0.0.0.0:8002", "--timeout", "60", "main:app"]
