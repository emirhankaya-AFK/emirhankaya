FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src src
RUN pip install --no-cache-dir .
COPY api api
COPY dashboard dashboard
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
